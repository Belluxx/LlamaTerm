import os
import sys
import re
import pygments
from pygments.lexers.markup import MarkdownLexer
from pygments.formatters import Terminal256Formatter
from dotenv import load_dotenv
from llama_cpp import Llama
from utils.ansi import AnsiCodes as AC
from utils.chat import Chat

load_dotenv('.env')

EXIT = 'exit'
SYSTEM_TAG = 'system'
USER_TAG = 'user'
ASSISTANT_TAG = 'assistant'

SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT')
ASSISTANT_INITIAL_MESSAGE = os.getenv('ASSISTANT_INITIAL_MESSAGE')
PREFIX_TEMPLATE = os.getenv('PREFIX_TEMPLATE')
N_GENERATE = int(os.getenv('N_GENERATE'))
EOS = os.getenv('EOS')

SYSTEM_DN = f'{AC.FG_CYAN}{AC.BOLD}System{AC.RESET}'
USER_DN = f'{AC.FG_RED}{AC.BOLD}User{AC.RESET}'
ASSISTANT_DN = f'{AC.FG_YELLOW}{AC.BOLD}Assistant{AC.RESET}'
INFO_DN = f'{AC.FG_GREEN}{AC.BOLD}Info{AC.RESET}'

BEGIN_USER = PREFIX_TEMPLATE.replace('{agent}', USER_TAG)
BEGIN_ASSISTANT = PREFIX_TEMPLATE.replace('{agent}', ASSISTANT_TAG)
BEGIN_SYSTEM = PREFIX_TEMPLATE.replace('{agent}', SYSTEM_TAG)
WORKING_DIR = sys.argv[1] if len(sys.argv) == 2 else os.getcwd()
CONTEXT_WARNING = min(500, N_GENERATE)


def format_text(text: str) -> str:
    lexer = MarkdownLexer()
    formatter = Terminal256Formatter(bg='dark')

    return pygments.highlight(text, lexer, formatter)


def inject_file(text: str) -> str:
    match_filename = r'\[(\S*\.\S+)\]'  # TODO Support spaces
    pattern = re.compile(match_filename)
    filenames: list[str] = pattern.findall(text)

    new_text = text
    for filename in filenames:
        filepath = WORKING_DIR + '/' + filename
        if os.path.isfile(filepath):
            print(f'{INFO_DN}: Injecting {filename} into the context.')
            new_text += f'\n\n{file_to_markdown(filename)}'
            continue
        print(f'{INFO_DN}: Faled injecting: {filename} does not exist.')
        new_text += f'\n\nFile {filename} does not exist.'
    
    return new_text


def file_to_markdown(filename: str) -> str:
    path = WORKING_DIR + '/' + filename
    extension = os.path.splitext(filename)[1][1:]
    with open(path, 'r') as f:
        text = f.read().strip()
    return f'Content of {filename}:\n```{extension}\n{text}\n```'


if __name__ == '__main__':
    print(f'{INFO_DN}: Loading model: {os.getenv("MODEL_PATH").split("/")[-1]}')
    llama = Llama(
        model_path=os.getenv('MODEL_PATH'),
        seed=int(os.getenv('SEED')),
        use_mlock=True,
        n_ctx=int(os.getenv('N_CTX')),
        n_gpu_layers=-1,
        verbose=False
    )

    prefixes = {
        'system': BEGIN_SYSTEM,
        'assistant': BEGIN_ASSISTANT,
        'user': BEGIN_USER
    }

    chat = Chat(
        model=llama,
        prefixes=prefixes,
        eos=EOS,
        n_generate=N_GENERATE,
        debug=False
    )

    chat.add_message(role=SYSTEM_TAG, content=SYSTEM_PROMPT)
    print(f'{SYSTEM_DN}: {SYSTEM_PROMPT}')
    chat.add_message(role=ASSISTANT_TAG, content=ASSISTANT_INITIAL_MESSAGE)
    print(f'{ASSISTANT_DN}: {ASSISTANT_INITIAL_MESSAGE}')

    last_message = ''
    try:
        while 1:
            last_message = input(f'{USER_DN}: ').strip()
            if len(last_message) == 0: continue
            if last_message == EXIT: break

            last_message = inject_file(last_message)
            free_ctx = chat.add_message(USER_TAG, last_message)
            if free_ctx <= CONTEXT_WARNING:
                print(f'{INFO_DN}: context is nearly finished ({free_ctx} tokens left)')
            
            print(f'{ASSISTANT_DN}: ', end='', flush=True)
            reply, free_ctx = chat.generate_reply()
            print(format_text(reply))
    except KeyboardInterrupt:
        print()
    
    chat.print_stats()


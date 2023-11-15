import os
import sys
import re
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


def format_text(text: str) -> str:
    match_block_start = r'```[A-Za-z]+'
    match_block_end = r'```'
    match_inline_block = r'`([^\n`]{2,}?)`'

    formatted_text = text
    formatted_text = re.sub(match_block_start, AC.BG_GREY1, formatted_text)
    formatted_text = re.sub(match_block_end, AC.RESET, formatted_text)
    formatted_text = re.sub(match_inline_block, fr'{AC.BG_GREY2}\1{AC.RESET}', formatted_text)

    return formatted_text


def inject_file(text: str) -> str:
    match_filename = r'\[(\S*\.\S+)\]'
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
    with open(path, 'r') as f:
        text = f.read().strip()
    return f'Content of {filename}:\n```{os.path.splitext(filename)[1][1:]}\n{text}\n```'


if __name__ == '__main__':
    llama = Llama(
        model_path=os.getenv('MODEL_PATH'),
        seed=69,
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
        n_generate=N_GENERATE
    )

    chat.add_message(role=SYSTEM_TAG, content=SYSTEM_PROMPT)
    print(f'{SYSTEM_DN}: {SYSTEM_PROMPT}')
    chat.add_message(role=ASSISTANT_TAG, content=ASSISTANT_INITIAL_MESSAGE)
    print(f'{ASSISTANT_DN}: {ASSISTANT_INITIAL_MESSAGE}')

    last_message = ''
    while 1:
        last_message = input(f'{USER_DN}: ').strip()
        if len(last_message) == 0: continue
        if last_message == EXIT: break

        last_message = inject_file(last_message)
        chat.add_message(USER_TAG, last_message)
        
        print(f'{ASSISTANT_DN}: ', end='', flush=True)
        reply = chat.generate_reply()
        print(format_text(reply))
    
    chat.print_stats()


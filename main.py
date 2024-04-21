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

DEBUG = False
ENV_FILE = '.env'
EXIT = 'exit'
ERROR_DN = f'{AC.FG_RED}{AC.BOLD}Error{AC.RESET}'

def throw_error(msg: str, code: int = 1) -> None:
    print(f'{ERROR_DN}: {msg}')
    exit(code)

def get_env_and_check(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        throw_error(f'missing .env field \'{key}\'', 2)

    return str(value)

# Check if .env exists and load it
if os.path.isfile(ENV_FILE):
    load_dotenv(ENV_FILE)
else:
    throw_error('cannot read .env file.')

# Load .env variables
MODEL_PATH = get_env_and_check('MODEL_PATH')
BOT = get_env_and_check('BOT')
PREFIX_TEMPLATE = get_env_and_check('PREFIX_TEMPLATE')
EOS = get_env_and_check('EOS')
AGENT_SYSTEM = get_env_and_check('AGENT_SYSTEM')
AGENT_USER = get_env_and_check('AGENT_USER')
AGENT_ASSISTANT = get_env_and_check('AGENT_ASSISTANT')
SYSTEM_PROMPT = get_env_and_check('SYSTEM_PROMPT')
ASSISTANT_INITIAL_MESSAGE = get_env_and_check('ASSISTANT_INITIAL_MESSAGE')
REAL_TIME = bool(int(get_env_and_check('REAL_TIME')))
N_CTX = int(get_env_and_check('N_CTX'))
N_GENERATE = int(get_env_and_check('N_GENERATE'))
SEED = int(get_env_and_check('SEED'))
USE_MMAP = bool(int(get_env_and_check('USE_MMAP')))
USE_MLOCK = bool(int(get_env_and_check('USE_MLOCK')))
USE_GPU = bool(int(get_env_and_check('USE_GPU')))

SYSTEM_DN = f'{AC.FG_CYAN}{AC.BOLD}System{AC.RESET}'
USER_DN = f'{AC.FG_RED}{AC.BOLD}User{AC.RESET}'
ASSISTANT_DN = f'{AC.FG_YELLOW}{AC.BOLD}Assistant{AC.RESET}'
INFO_DN = f'{AC.FG_GREEN}{AC.BOLD}Info{AC.RESET}'

BEGIN_USER = PREFIX_TEMPLATE.replace('{agent}', AGENT_USER)
BEGIN_ASSISTANT = PREFIX_TEMPLATE.replace('{agent}', AGENT_ASSISTANT)
BEGIN_SYSTEM = PREFIX_TEMPLATE.replace('{agent}', AGENT_SYSTEM)
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
    print(f'{INFO_DN}: Loading model: {MODEL_PATH.split("/")[-1]}')
    try:
        llama = Llama(
            model_path=MODEL_PATH,
            seed=SEED,
            use_mlock=USE_MLOCK,
            use_mmap=USE_MMAP,
            n_ctx=N_CTX,
            n_gpu_layers=-1 if USE_GPU else 0,
            verbose=DEBUG
        )
    except ValueError as e:
        throw_error(f"the model path specified in the .env file is not valid: '{MODEL_PATH}'")

    prefixes = {
        'system': BEGIN_SYSTEM,
        'assistant': BEGIN_ASSISTANT,
        'user': BEGIN_USER
    }

    agents = {
        'system': AGENT_SYSTEM,
        'assistant': AGENT_ASSISTANT,
        'user': AGENT_USER
    }

    chat = Chat(
        model=llama,
        prefixes=prefixes,
        agents=agents,
        bot=BOT,
        eos=EOS,
        n_generate=N_GENERATE,
        debug=DEBUG
    )

    chat.add_message(agent=AGENT_SYSTEM, content=SYSTEM_PROMPT)
    print(f'{SYSTEM_DN}: {SYSTEM_PROMPT}')
    chat.add_message(agent=AGENT_ASSISTANT, content=ASSISTANT_INITIAL_MESSAGE)
    print(f'{ASSISTANT_DN}: {ASSISTANT_INITIAL_MESSAGE}')

    last_message = ''
    try:
        while 1:
            last_message = input(f'{USER_DN}: ').strip()
            if len(last_message) == 0: continue
            if last_message == EXIT: break

            last_message = inject_file(last_message)
            free_ctx = chat.add_message(AGENT_USER, last_message)
            if free_ctx <= CONTEXT_WARNING:
                print(f'{INFO_DN}: context is nearly finished ({free_ctx} tokens left)')

            print(f'{ASSISTANT_DN}: ', end='', flush=True)
            if not REAL_TIME:
                reply, free_ctx = chat.generate_reply()
                print(format_text(reply))
            else:
                for token in chat.generate_reply_stepped():
                    print(token, end='', flush=True)
                    free_ctx -= 1  # TODO Check if correct for EOS fixes that do not count as additional tokens
    except KeyboardInterrupt:
        print()

    chat.print_stats()
    if DEBUG: print(chat.get_raw_chat())

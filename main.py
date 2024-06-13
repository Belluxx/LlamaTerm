import os
import sys
import re
import pathlib
import pygments
from pygments.lexers.markup import MarkdownLexer
from pygments.formatters import Terminal256Formatter
from dotenv import load_dotenv
from llama_cpp import Llama
from utils.ansi import AnsiCodes as AC
from utils.chat import Chat

COMMAND_EXIT = 'exit'
COMMAND_RESTART = 'restart'

DEBUG = False
ENV_FILE = '.env'
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
MODEL_PATH =                get_env_and_check('MODEL_PATH')
BOT =                       get_env_and_check('BOT')
PREFIX_TEMPLATE =           get_env_and_check('PREFIX_TEMPLATE')
EOS =                       get_env_and_check('EOS')
AGENT_SYSTEM =              get_env_and_check('AGENT_SYSTEM')
AGENT_USER =                get_env_and_check('AGENT_USER')
AGENT_ASSISTANT =           get_env_and_check('AGENT_ASSISTANT')
SYSTEM_PROMPT =             get_env_and_check('SYSTEM_PROMPT')
ASSISTANT_INITIAL_MESSAGE = get_env_and_check('ASSISTANT_INITIAL_MESSAGE')
REAL_TIME =                 bool(int(get_env_and_check('REAL_TIME')))
N_CTX =                     int(get_env_and_check('N_CTX'))
N_GENERATE =                int(get_env_and_check('N_GENERATE'))
SEED =                      int(get_env_and_check('SEED'))
USE_MMAP =                  bool(int(get_env_and_check('USE_MMAP')))
USE_MLOCK =                 bool(int(get_env_and_check('USE_MLOCK')))
USE_GPU =                   bool(int(get_env_and_check('USE_GPU')))

SYSTEM_DN =                 f'{AC.FG_CYAN}{AC.BOLD}System{AC.RESET}'
USER_DN =                   f'{AC.FG_RED}{AC.BOLD}User{AC.RESET}'
ASSISTANT_DN =              f'{AC.FG_YELLOW}{AC.BOLD}Assistant{AC.RESET}'
INFO_DN =                   f'{AC.FG_GREEN}{AC.BOLD}Info{AC.RESET}'

BEGIN_USER =                PREFIX_TEMPLATE.replace('{agent}', AGENT_USER)
BEGIN_ASSISTANT =           PREFIX_TEMPLATE.replace('{agent}', AGENT_ASSISTANT)
BEGIN_SYSTEM =              PREFIX_TEMPLATE.replace('{agent}', AGENT_SYSTEM)
WORKING_DIR =               sys.argv[1] if len(sys.argv) == 2 else os.getcwd()
CONTEXT_WARNING =           min(500, N_GENERATE)


def format_text(text: str) -> str:
    lexer = MarkdownLexer()
    formatter = Terminal256Formatter(bg='dark')

    return pygments.highlight(text, lexer, formatter)


def inject_file(text: str) -> str:  # TODO Check if path is absolute. If so, don't append the working dir
    match_filename = r'\[(([^\[\]])+\.(\w|\d){1,10})\]'
    pattern = re.compile(match_filename)
    filepaths: list[str] = [p[0] for p in pattern.findall(text)]
    if DEBUG: print(f'{INFO_DN}: filepaths detected in prompt: {str(filepaths)}')

    new_text = text
    for file_path in filepaths:
        file_full_path = file_path
        if not os.path.isabs(file_path):
            file_full_path = os.path.join(WORKING_DIR, file_path)
        if DEBUG: print(f'{INFO_DN}: full path is "{file_full_path}"')

        if not os.path.isfile(file_full_path):
            print(f'{ERROR_DN}: faled injecting: "{file_path}" does not exist.')
            new_text += f'\n\nFile "{file_path}" does not exist.'
            continue

        print(f'{INFO_DN}: injecting "{file_path}" into the context.')
        to_inject = file_to_markdown(file_full_path)
        new_text += '\n\n' + to_inject

    return new_text


def file_to_markdown(file_path: str) -> str:
    path_split = os.path.splitext(file_path)
    file_ext = os.path.splitext(file_path)[1][1:]
    file_name = path_split[0].split(os.sep)[-1] + '.' + file_ext


    with open(file_path, 'r') as f:
        text = f.read().strip()

    md = f'Content of {file_name}:\n```{file_ext}\n{text}\n```'
    if DEBUG: print(f'{INFO_DN}: file markdown: {md}')

    return md


if __name__ == '__main__':
    print(f'{INFO_DN}: loading model: {MODEL_PATH.split("/")[-1]}')
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
        throw_error(f'the model path specified in the .env file is not valid: "{MODEL_PATH}"')

    agent_prefixes = {
        'system': BEGIN_SYSTEM,
        'assistant': BEGIN_ASSISTANT,
        'user': BEGIN_USER
    }

    agent_names = {
        'system': AGENT_SYSTEM,
        'assistant': AGENT_ASSISTANT,
        'user': AGENT_USER
    }

    chat = Chat(
        model=llama,
        agent_prefixes=agent_prefixes,
        agent_names=agent_names,
        bot=BOT,
        eos=EOS,
        n_generate=N_GENERATE,
        debug=DEBUG
    )

    chat.send_message(agent=Chat.SYSTEM_KEY, content=SYSTEM_PROMPT)
    print(f'{SYSTEM_DN}: {SYSTEM_PROMPT}')
    chat.send_message(agent=Chat.ASSISTANT_KEY, content=ASSISTANT_INITIAL_MESSAGE)
    print(f'{ASSISTANT_DN}: {ASSISTANT_INITIAL_MESSAGE}')

    last_message = ''
    try:
        while 1:
            last_message = input(f'{USER_DN}: ').strip()
            if len(last_message) == 0: continue
            if last_message == COMMAND_EXIT: break
            if last_message == COMMAND_RESTART:
                chat.reset_chat(keep_system=True)
                print(f'{INFO_DN}: chat context cleared successfully')
                continue

            last_message = inject_file(last_message)
            free_ctx = chat.send_message(Chat.USER_KEY, last_message)
            if free_ctx <= CONTEXT_WARNING:
                print(f'{INFO_DN}: context is nearly finished ({free_ctx} tokens left)')

            print(f'{ASSISTANT_DN}: ', end='', flush=True)
            if not REAL_TIME:
                reply, free_ctx = chat.generate_assistant_reply()
                print(format_text(reply))
            else:
                for token in chat.generate_assistant_reply_stepped():
                    print(token, end='', flush=True)
                    free_ctx -= 1
                    # TODO Get free ctx from apposite chat method
    except KeyboardInterrupt:
        print()

    chat.print_stats()
    if DEBUG: print(chat.get_raw_chat())

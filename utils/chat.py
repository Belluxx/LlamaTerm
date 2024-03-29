from time import time
from llama_cpp import Llama


class Message:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content


class Chat:

    CLEAR_CURRENT_LINE = '\33[2K\r'
    CHARSET = 'UTF-8'

    def __init__(
            self,
            model: Llama,
            prefixes: dict[str, str],
            eos: str,
            agents: dict[str, str] = {
                'system': 'system',
                'assistant': 'assistant',
                'user': 'user'
            },
            n_generate=1000,
            debug=False
    ) -> None:
        self.model = model
        self.agents = agents
        self.prefixes = prefixes
        self.eos = eos
        self.n_generate = n_generate
        self.debug = debug
        self.messages: list[Message] = []
        self.tokens: list[int] = []
        self.generation_time = 0
        self.n_tokens_generated = 0


    def add_message(self, agent: str, content: str) -> int:
        new_message = Message(role=agent, content=content)
        self.messages.append(new_message)

        wrapped_content: str = new_message.content + self.eos
        if agent == self.agents['system']:
            wrapped_content = f'{self.prefixes["system"]}\n{wrapped_content}\n{self.prefixes["assistant"]}\n'
        elif agent == self.agents['assistant']:
            wrapped_content = f'{wrapped_content}\n{self.prefixes["user"]}\n'
        elif agent == self.agents['user']:
            wrapped_content = f'{wrapped_content}\n{self.prefixes["assistant"]}\n'

        new_tokens = self.tokenize_text(wrapped_content)
        self.tokens += new_tokens

        return self.context_available()


    def generate_reply(self) -> tuple[str, int]:
        full_reply = ""
        n_current_tokens = 0
        free_context = self.context_available()

        if free_context <= 0:
            self.context_exceeded()

        start_time = time()
        for token in self.model.generate(tokens=self.tokens):
            if self.debug: print(f'{token}\t{self.detokenize_text([token])}')
            if token == self.model.token_eos():
                break
            if n_current_tokens >= self.n_generate:
                break
            if free_context - n_current_tokens <= 0:
                self.context_exceeded()

            self.append_raw_tokens([token])

            reply = self.detokenize_text([token])
            full_reply += reply

            interrupt, full_reply = self.check_eos_failure(full_reply)
            if interrupt: break

            interrupt, full_reply = self.check_model_impersonation(full_reply, 'user')
            if interrupt: break

            interrupt, full_reply = self.check_model_impersonation(full_reply, 'system')
            if interrupt: break

        self.append_raw_text(f'\n{self.prefixes["user"]}\n')  # TODO Temporary fix for missing user prefix

        self.generation_time += time() - start_time
        self.n_tokens_generated += n_current_tokens

        return full_reply, self.context_available()


    def generate_reply_stepped(self):
        full_reply = ""
        n_current_tokens = 0
        free_context = self.context_available()

        if free_context <= 0:
            self.context_exceeded()

        start_time = time()
        for token in self.model.generate(tokens=self.tokens):
            if token == self.model.token_eos():
                yield '\n'
                break
            if n_current_tokens >= self.n_generate:
                yield '\n'
                break
            if free_context - n_current_tokens <= 0:
                self.context_exceeded()

            self.append_raw_tokens([token])

            reply = self.detokenize_text([token])
            full_reply += reply

            interrupt, full_reply = self.check_eos_failure(full_reply)
            if interrupt:
                n_char_to_delete = len(self.eos) - 1
                back_str = '\b' * n_char_to_delete
                empty_str = ' ' * n_char_to_delete
                yield back_str + empty_str + '\n'
                break

            interrupt, full_reply = self.check_model_impersonation(full_reply, 'user')
            if interrupt:
                yield self.CLEAR_CURRENT_LINE
                break

            interrupt, full_reply = self.check_model_impersonation(full_reply, 'system')
            if interrupt:
                yield self.CLEAR_CURRENT_LINE
                break

            yield reply

        self.append_raw_text(f'\n{self.prefixes["user"]}\n')  # TODO Temporary fix for missing user prefix

        self.generation_time += time() - start_time
        self.n_tokens_generated += n_current_tokens


    def check_eos_failure(self, full_reply: str) -> tuple[bool, str]:
        interrupt = False
        if self.eos in full_reply[-(len(self.eos)+1):]:
            if self.debug: print(f'[DEBUG] EOS escape occurred: {full_reply[-len(self.eos):]}')
            full_reply = full_reply[:-len(self.eos)]
            interrupt = True

        return interrupt, full_reply


    def check_model_impersonation(self, full_reply: str, agent: str) -> tuple[bool, str]:
        interrupt = False
        if self.prefixes[agent] in full_reply:
            if self.debug: print(f'[DEBUG] Impersonation of {agent} detected')
            full_reply = full_reply.split(self.prefixes[agent])[0].strip()
            interrupt = True

        return interrupt, full_reply


    def detokenize_text(self, tokens: list[int]) -> str:
        errors_strategy = 'ignore'
        try:
            return self.model.detokenize(tokens).decode(self.CHARSET, errors=errors_strategy)
        except:
            print('[ERROR] An error occurred during detokenization of:', tokens)
            exit(3)


    def tokenize_text(self, text: str) -> list[int]:
        return self.model.tokenize(bytes(text, self.CHARSET), add_bos=False)


    def tokens_used(self) -> int:
        return len(self.tokens)


    def context_available(self) -> int:
        return self.model.n_ctx() - self.tokens_used()


    def context_exceeded(self):
        print('[ERROR] Context exceeded.')
        exit(0)


    def print_stats(self):
        if self.generation_time == 0: return
        print(f'Tokens used: {self.tokens_used()}')
        print(f'Tokens left: {self.context_available()}')
        print(f'Tokens generated per second: {self.n_tokens_generated / self.generation_time:.2f}')


    def append_raw_text(self, new_text: str):
        self.append_raw_tokens(self.tokenize_text(new_text))


    def append_raw_tokens(self, new_tokens: list[int]):
        self.tokens += new_tokens
        self.n_tokens_generated += len(new_tokens)


    def get_raw_chat(self) -> str:
        return self.model.detokenize(self.tokens).decode("UTF-8")


    def delete(self):
        del self.model

from llama_cpp import Llama, LlamaGrammar


class Message:
    def __init__(self, agent: str, content: str) -> None:
        self.agent = agent
        self.content = content


class Chat:

    CLEAR_CURRENT_LINE = '\33[2K\r'
    CHARSET = 'UTF-8'

    def __init__(
            self,
            model: Llama,
            bot: str,
            eos: str,
            n_generate: int,
            agent_prefixes: dict[str, str] = {
                'system': '<|im_start|>system',
                'assistant': '<|im_start|>assistant',
                'user': '<|im_start|>user'
            },
            agent_names: dict[str, str] = {
                'system': 'system',
                'assistant': 'assistant',
                'user': 'user'
            },
            debug=False
    ) -> None:
        """
        Create a new Chat object

        @param model: the llama object that represents the model
        @param bot: the token that starts the chat
        @param eos: the token that ends a single chat round
        @param n_generate: the maximum number of tokens generated by the model in a single turn
        @param agent_prefixes: the tokens used to wrap an agent name
        @param agent_names: the dict with the names for: system, assistant, user
        @param debug: whether or not to output debug informations
        """
        self.model = model
        self.bot = bot
        self.eos = eos
        self.n_generate = n_generate
        self.agent_prefixes = agent_prefixes
        self.agent_names = agent_names
        self.debug = debug

        self.messages: list[Message] = []
        self.tokens_cache: list[int] = []

        if len(self.bot) > 0:  # Add the BOT (Begin Of Text) if specified
            self.tokens_cache += self.tokenize_text(self.bot)


    def generate_assistant_reply(self, grammar: LlamaGrammar | None = None) -> tuple[str, int]:
        self.cache_append_header(agent='assistant')

        reply = ''
        n_reply_tokens = 0
        for token in self.model.generate(tokens=self.tokens_cache, grammar=grammar):
            self.check_context_overflow()                   # Check for context exceeded
            if token == self.model.token_eos(): break       # Check for EOS termination
            if n_reply_tokens >= self.n_generate: break     # Check for max tokens reached

            self.tokens_cache.append(token)
            n_reply_tokens += 1
            reply += self.detokenize_tokens([token])

            interrupt, reply = self.check_eos_failure(reply)                    # Check for EOS detection failure due to multiple EOS tokens
            if interrupt: break
            interrupt, reply = self.check_model_impersonation(reply, 'user')    # Check for model trying to impersonate the user before EOS
            if interrupt: break
            interrupt, reply = self.check_model_impersonation(reply, 'system')  # Check for model trying to impersonate the system before EOS
            if interrupt: break

        return reply, self.context_available()


    def generate_assistant_reply_stepped(self, grammar: LlamaGrammar | None = None):
        self.cache_append_header(agent='assistant')

        reply = ''
        n_reply_tokens = 0
        for token in self.model.generate(tokens=self.tokens_cache, grammar=grammar):
            self.check_context_overflow()
            if token == self.model.token_eos(): yield '\n'; break
            if n_reply_tokens >= self.n_generate: yield '\n'; break

            self.tokens_cache.append(token)
            n_reply_tokens += 1
            new_text = self.detokenize_tokens([token])
            reply += new_text

            interrupt, reply = self.check_eos_failure(reply)
            if interrupt:  # Remove the broken EOS text from the terminal
                n_char_to_delete = len(self.eos) - 1
                back_str = '\b' * n_char_to_delete
                empty_str = ' ' * n_char_to_delete
                yield back_str + empty_str + '\n'
                break
            interrupt, reply = self.check_model_impersonation(reply, 'user')
            if interrupt:  # Remove the text generated by the impersionation from the terminal
                yield self.CLEAR_CURRENT_LINE
                break
            interrupt, reply = self.check_model_impersonation(reply, 'system')
            if interrupt:  # Remove the text generated by the impersionation from the terminal
                yield self.CLEAR_CURRENT_LINE
                break

            yield new_text

        return reply, self.context_available()


    def add_message(self, agent: str, content: str) -> int:
        new_message = Message(agent=agent, content=content)
        self.messages.append(new_message)
        self.cache_update_last_msg()

        return self.context_available()


    def check_eos_failure(self, reply: str) -> tuple[bool, str]:
        interrupt = False
        if self.eos in reply[-(len(self.eos)+1):]:
            if self.debug: print(f'[DEBUG] EOS escape occurred: {reply[-len(self.eos):]}')
            reply = reply[:-len(self.eos)]
            interrupt = True

        return interrupt, reply


    def check_model_impersonation(self, reply: str, agent: str) -> tuple[bool, str]:
        interrupt = False
        if self.agent_prefixes[agent] in reply:
            if self.debug: print(f'[DEBUG] Impersonation of {agent} detected')
            reply = reply.split(self.agent_prefixes[agent])[0].strip()
            interrupt = True

        return interrupt, reply


    def cache_append_header(self, agent: str) -> None:
        header = f'{self.agent_prefixes[agent]}'
        self.tokens_cache += self.tokenize_text(header)


    def cache_update_last_msg(self) -> None:
        last_message = self.messages[-1]
        agent = last_message.agent
        round_text = f'{self.agent_prefixes[agent]}{last_message.content}{self.eos}'

        self.tokens_cache += self.tokenize_text(round_text)


    def cache_reload(self) -> None:
        pass


    def detokenize_tokens(self, tokens: list[int]) -> str:
        errors_strategy = 'ignore'
        try:
            return self.model.detokenize(tokens).decode(self.CHARSET, errors=errors_strategy)
        except:
            print('[ERROR] An error occurred during detokenization of:', tokens)
            exit(1)


    def tokenize_text(self, text: str, add_bos: bool = False) -> list[int]:
        try:
            return self.model.tokenize(text=bytes(text, self.CHARSET), add_bos=add_bos)
        except:
            print('[ERROR] An error occurred during tokenization of:', text)
            exit(1)


    def check_context_overflow(self):
        if self.context_available() <= 0:
            print('[ERROR] Context exceeded.')
            exit(1)


    def print_stats(self):
        print(f'Tokens used: {self.tokens_used()}')
        print(f'Tokens left: {self.context_available()}')


    def context_available(self) -> int:
        return self.model.n_ctx() - self.tokens_used()


    def tokens_used(self) -> int:
        return len(self.tokens_cache)


    def get_raw_chat(self) -> str:
        return self.detokenize_tokens(self.tokens_cache)

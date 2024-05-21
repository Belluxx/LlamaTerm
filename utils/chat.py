from llama_cpp import Llama, LlamaGrammar


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
            bot: str,
            eos: str,
            prefixes: dict[str, str],
            n_generate: int,
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
        @param prefixes: the tokens used to wrap an agent name
        @param agent_names: the dict with the names for: system, assistant, user
        @param debug: whether or not to output debug informations
        """
        self.model = model
        self.bot = bot
        self.eos = eos
        self.prefixes = prefixes
        self.n_generate = n_generate
        self.agent_names = agent_names
        self.debug = debug

        self.messages: list[Message] = []
        self.tokens_cache: list[int] = []


    def add_message(self, agent: str, content: str) -> int:
        new_message = Message(role=agent, content=content)
        self.messages.append(new_message)

        return self.context_available()


    def generate_reply(self, grammar: LlamaGrammar | None = None) -> tuple[str, int]:
        pass


    def generate_reply_stepped(self, grammar: LlamaGrammar | None = None):
        pass


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
            exit(1)


    def tokenize_text(self, text: str) -> list[int]:
        return self.model.tokenize(bytes(text, self.CHARSET), add_bos=False)


    def check_context_overflow(self):
        if self.context_available() <= 0
            print('[ERROR] Context exceeded.')
            exit(1)


    def print_stats(self):
        print(f'Tokens used: {self.tokens_used()}')
        print(f'Tokens left: {self.context_available()}')


    def context_available(self) -> int:
        return self.model.n_ctx() - self.tokens_used()


    def tokens_used(self) -> int:
        pass


    def delete(self):
        del self.model

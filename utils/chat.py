from time import time
from llama_cpp import Llama


class Message:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content


class Chat:
    def __init__(
            self,
            model: Llama,
            prefixes: dict[str, str],
            eos: str,
            tags: dict[str, str] = {
                'system': 'system',
                'assistant': 'assistant',
                'user': 'user'
            }, 
            n_generate=1000
    ) -> None:
        self.model = model
        self.tags = tags
        self.prefixes = prefixes
        self.eos = eos
        self.n_generate = n_generate
        self.messages: list[Message] = []
        self.tokens: list[int] = []
        self.generation_time = 0
        self.n_tokens_generated = 0


    def add_message(self, role: str, content: str):
        new_message = Message(role=role, content=content)
        self.messages.append(new_message)

        wrapped_content: str = new_message.content + self.eos
        if role == self.tags['system']:
            wrapped_content = f'{self.prefixes["system"]}\n{wrapped_content}\n{self.prefixes["assistant"]}\n'
        elif role == self.tags['assistant']:
            wrapped_content = f'{wrapped_content}\n{self.prefixes["user"]}\n'
        elif role == self.tags['user']:
            wrapped_content = f'{wrapped_content}\n{self.prefixes["assistant"]}\n'

        new_tokens = self.tokenize_text(wrapped_content)
        self.tokens += new_tokens

    
    def generate_reply(self) -> str:
        full_reply = ""
        n_current_tokens = 0
        free_context = self.context_available()

        if free_context <= 0:
            self.context_exceeded()
        
        start_time = time()
        for token in self.model.generate(tokens=self.tokens):
            if token == self.model.token_eos():
                break
            if n_current_tokens >= self.n_generate:
                break
            if free_context - n_current_tokens <= 0: 
                self.context_exceeded()
            
            self.tokens.append(token)
            n_current_tokens += 1

            reply = self.model.detokenize([token]).decode('UTF-8')
            full_reply += reply
            
            interrupt, full_reply = self.check_model_impersonation(full_reply, 'user')
            if interrupt: break

            interrupt, full_reply = self.check_model_impersonation(full_reply, 'system')
            if interrupt: break
            
        self.generation_time += time() - start_time
        self.n_tokens_generated += n_current_tokens

        return full_reply


    def check_model_impersonation(self, full_reply: str, actor: str) -> tuple[bool, str]:
        interrupt = False
        if self.prefixes[actor] in full_reply:
            full_reply = full_reply.split(self.prefixes[actor])[0].strip()
            interrupt = True
        return interrupt, full_reply


    def tokenize_text(self, text: str) -> list[int]:
        return self.model.tokenize(bytes(text, 'UTF-8'), add_bos=False)


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

# LlamaTerm
LlamaTerm is a simple CLI utility that allows to use local LLM models easily and with some additional features.
> :warning: Currently this project supports models that use ChatML format or something similar. Use for example [Phi-3-mini](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf) and [LLama3](https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF) GGUFs.

## Preview
### Basic usage:
<img src="https://raw.githubusercontent.com/Belluxx/LlamaTerm/main/static/example1.gif" height="300" />

### Injecting file content:
<img src="https://raw.githubusercontent.com/Belluxx/LlamaTerm/main/static/example2.gif" height="300" />

## Features
- Give local files to the model using square brackets\
`User: Can you explain the code in [helloworld.c] please?`
- More coming soon

## Setup
You can setup LLamaTerm by:
1) Rename `example.env` to `.env`
2) Modify `.env` so that the model path corresponds (you may also need to edit `EOS` and `PREFIX_TEMPLATE`)
3) If you need **syntax highlighting** for code and markdown, then set `REAL_TIME=0` in the `.env`. Note that you will lose real time output generation.
4) Install python dependencies with `pip install -r requirements.txt`
5) If you have a **CUDA GPU**: install with cuBLAS acceleration: `CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install --upgrade --force-reinstall --no-cache llama-cpp-python`
6) If you have an **AMD GPU**: install with HIP acceleration `CMAKE_ARGS="-DLLAMA_HIPBLAS=on -DAMDGPU_TARGETS=insert gpu arch or compatible arch" FORCE_CMAKE=1 CXX=/opt/rocm/bin/hipcc pip install llama-cpp-python --upgrade --force-reinstall --no-cache`. For more info see [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)

## Run
Run LlamaTerm by adding the project directory to the `PATH` and then running `llamaterm`

## Models supported out of the box
For the following models you will just need to rename the corresponding example `example-*.env` file to `.env`:
* [LLama3 8B Instruct](https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF) [**RECOMMENDED**]
* [Phi 3 Mini Instruct](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf) [**RECOMMENDED**]
* [OpenHermes 2.5 Mistral 7B GGUF](https://huggingface.co/TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/tree/main)
* [Zephyr Beta 7B GGUF](https://huggingface.co/TheBloke/zephyr-7B-beta-GGUF/tree/main)

All the other models that have a prompt template similar to ChatML are supported but you will need to customize some fields like `PREFIX_TEMPLATE`, `EOS` etc... in the `.env`.

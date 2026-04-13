from mcp.server import FastMCP

app = FastMCP('prompt_and_resources')

@app.prompt('翻译专家')
async def translate_expert(
        target_language: str = 'Chinese',
) -> str:
    return f'你是一个翻译专家，擅长将任何语言翻译成{target_language}。请翻译以下内容：'

@app.resource('echo://static')
async def echo_resource():
    # 返回的是，当用户使用这个资源时，资源的内容
    return 'Echo!'

@app.resource('greeting://{name}')
async def get_greeting(name):
    return f'Hello, {name}!'

if __name__ == '__main__':
    app.run(transport='stdio')

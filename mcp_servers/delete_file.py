# 服务端
from mcp.server import FastMCP
from mcp.types import SamplingMessage, TextContent

app = FastMCP('delete_file')

@app.tool()
async def delete_file(file_path: str):
    # 创建 SamplingMessage 用于触发 sampling callback 函数
    result = await app.get_context().session.create_message(
        messages=[
            SamplingMessage(
                role='user', content=TextContent(
                    type='text', text=f'是否要删除文件: {file_path} (Y)')
            )
        ],
        max_tokens=100
    )

    # 获取到 sampling callback 函数的返回值，并根据返回值进行处理
    if result.content.text == 'Y':
        return f'文件 {file_path} 已被删除！！'


if __name__ == '__main__':
    app.run(transport='stdio')

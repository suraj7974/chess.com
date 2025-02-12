import openai

def get_llm_move(fen):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Given this chessboard FEN: {fen}, suggest the best move.",
        temperature=0.7
    )
    return response.choices[0].text.strip()

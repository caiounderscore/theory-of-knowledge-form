from datetime import datetime
import json
from chalice import Chalice, Response
import boto3

from backend.constants import QUESTIONS

app = Chalice(app_name='knowledge-test')


# Endpoint 1: Buscar perguntas
@app.route('/get-questions', methods=['GET'], cors=True)
def get_questions():
    return QUESTIONS

# Endpoint 2: Processar respostas e gerar gráfico
@app.route('/process-answers', methods=['POST'], cors=True)
def process_answers():
    request = app.current_request
    body = request.json_body  
    interviewed = body.get("interviewed", "unknown")

    # Save the answers in s3
    s3 = boto3.client('s3')
    today = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')

    # Respostas enviadas pelo frontend
    answers = body.get("answers", [])

    score = calculate_scores(answers)
    # Calcular as pontuações para cada eixo
    payload_to_save = {
        "interviewed": interviewed,
        "score": score,
        "answers": answers
    }
    s3.put_object(Bucket='knowledge-test-answers', Key=f'{interviewed["name"]}_{interviewed["age"]}-{today}.json', Body=json.dumps(payload_to_save))

    return score


    # Gerar gráfico 3D
    img_base64 = generate_3d_plot(scores)


# Mapeamento do tipo de conhecimento para eixos e direção
knowledge_to_axis = {
    1: ("x", 1),  
    2: ("x", -1), 
    3: ("y", 1),
    4: ("y", -1), 
    5: ("z", -1),
    6: ("z", 1)  
}

def calculate_scores(answers):
    # Inicializa os valores para os eixos e contadores
    scores = {"x": 0, "y": 0, "z": 0}
    max_possible_scores = {"x": 0, "y": 0, "z": 0}  # Para normalização posterior

    for answer in answers:
        question_id = answer["id"]
        score = int(answer["score"])  # Escala de 0 a 100

        # Mapeia a pergunta para o eixo e direção
        knowledge_type = next(q for q in QUESTIONS["questions"] if q["id"] == question_id)["knowledge"]
        axis, direction = knowledge_to_axis[knowledge_type]

        # Ajusta o valor da resposta baseado na direção (positivo ou negativo)
        adjusted_score = direction * (score - 50)  # Neutro (50) não impacta, positivo ou negativo ajusta o espectro

        # Atualiza o score para o eixo correspondente
        scores[axis] += adjusted_score

        # Atualiza o máximo possível para normalização
        max_possible_scores[axis] += 50  # Cada pergunta contribui no máximo ±50 em ambos os lados

    # Calcula o percentual final para cada eixo
    percentages = {}
    for axis in scores:
        if max_possible_scores[axis] > 0:
            # Percentual é proporcional à soma das respostas ajustadas
            percentages[axis] = ((scores[axis] + max_possible_scores[axis]) / (2 *max_possible_scores[axis])) * 100
        else:
            percentages[axis] = 50  # Caso não haja perguntas no eixo, assume-se neutro (50%)

    if percentages["z"] > 50:
        percentages["z"] = 50


    return percentages
# Função para gerar gráfico 3D
# def generate_3d_plot(scores):
#     fig = plt.figure(figsize=(10, 8))
#     ax = fig.add_subplot(111, projection='3d')

#     # Ponto do participante
#     ax.scatter(scores["x"], scores["y"], scores["z"], color="blue", s=100, label="Você")

#     # Linhas dos eixos
#     ax.plot([0, 0], [0, 0], [-1, 1], color="black", linestyle="--", linewidth=0.8)  # Z-axis
#     ax.plot([0, 0], [-1, 1], [0, 0], color="black", linestyle="--", linewidth=0.8)  # Y-axis
#     ax.plot([-1, 1], [0, 0], [0, 0], color="black", linestyle="--", linewidth=0.8)  # X-axis

#     # Rótulos dos eixos
#     ax.set_xlabel("Empirismo <--> Racionalismo", fontsize=6)
#     ax.set_ylabel("Relativismo <--> Realismo Absoluto", fontsize=6)
#     ax.set_zlabel("Pragmatista <--> Contemplativo", fontsize=6)

#     # Ajustes de visualização
#     ax.view_init(elev=20, azim=30)

#     # Salvar gráfico em memória e converter para Base64
#     img = io.BytesIO()
#     plt.savefig(img, format='png', bbox_inches='tight')
#     img.seek(0)
#     img_base64 = base64.b64encode(img.read()).decode('utf-8')
#     plt.close()

#     return img_base64

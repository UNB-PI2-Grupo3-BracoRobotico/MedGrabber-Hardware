import sys
import argparse
import json
import logging
from datetime import datetime

from transitions import Machine, State
from confluent_kafka import Consumer, Producer

# from RPiMotorLib import A4988Nema
import RPi.GPIO as GPIO

# import picamera
import time


logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configurações do Kafka
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
# KAFKA_TOPIC = 'nome_do_topico'

# Definição de tamanho das caixas:
Aberto  = 180
G       = 150  # Angulo para que o servo pegue a caixa Pequena
M       = 120  # Angulo para que o servo pegue a caixa Média
P       = 80   # Angulo para que o servo pegue a caixa Grande
Fechado = 0
oldx = 0  # Para teste de validade de x
oldy = 0  # Para teste de validade de y

# Definindo as portas:
A_PIN       = 19  # Pino para o seletor A
B_PIN       = 20  # Pino para o seletor B
C_PIN       = 26  # Pino para o seletor C
INHIBIT_PIN = 21  # Pino para inibir os DEMUX
ENABLE_PIN  = 23  # Pino para ativação dos Enable dos motores
STEP_PIN    = 12  # Pino para o PWM (step) dos motores de passo e servo motor
DIR_PIN     = 24  # Pino para a direção dos motores de passo
MS1_PIN     = 17  # Pino para a resolução de MicroPasso 1
MS2_PIN     = 27  # Pino para a resolução de MicroPasso 2
MS3_PIN     = 22  # Pino para a resolução de MicroPasso 3
GPIO16      = 16  # Pino para o reset/sleep dos drivers do motor de passo
SERVO_PIN   = 13  # Pino para dados do Servo

# Pré-definições importantes:
GPIO.setwarnings(False)

# Inicialize a biblioteca RPi.GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(A_PIN, GPIO.OUT)
GPIO.setup(B_PIN, GPIO.OUT)
GPIO.setup(C_PIN, GPIO.OUT)
GPIO.setup(INHIBIT_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(MS1_PIN, GPIO.OUT)
GPIO.setup(MS2_PIN, GPIO.OUT)
GPIO.setup(MS3_PIN, GPIO.OUT)
GPIO.setup(GPIO16, GPIO.OUT)
servo = GPIO.PWM(SERVO_PIN, 50) # Para configuração do Servo. 50Hz(20ms)

# Iniciando o servo da garra:
servo.start(0)
servo.ChangeDutyCycle(2)

# Selecionando saída do demux:
# CH 0 -> CBA = 000
# CH 1 -> CBA = 001
# CH 2 -> CBA = 010

# X: HIGH = Esquerda e LOW = Direita
# Y: HIGH = Sobe e LOW = Desce
# Z: HIGH = Frente(Dentro) e LOW = Trás(Fora)

Cima        = 'GPIO.HIGH'
Baixo       = 'GPIO.LOW'
Esquerda    = 'GPIO.HIGH'
Direita     = 'GPIO.LOW'
Frente      = 'GPIO.HIGH'
Tras        = 'GPIO.LOW'

# Configurações para o controle do motor de passo
DutyCycle = 0.002  # Delay entre os pulsos (segundos) -> 1ms = 1KHz
DutyCycleS = 0.00152  # Delay entre os pulsos (segundos) -> 1ms = 1KHz
STEPS_PER_REV = 200  # Quantidade de passos para uma rotação completa
DISTANCE_PER_REV = 4  # Distância percorrida em uma rotação completa (cm)
# Ou seja, 50 passos por cm andado. Cada passo andará 0,2 mm.

# Função para posicionar o servo em um ângulo específico
def set_servo_angle(angle):
    duty_cycle = (angle / 18) + 2
    servo.ChangeDutyCycle(duty_cycle)
    # pulse_duration = (angle / 45) * 400  # Cálculo da duração do pulso em microssegundos
    # duty_cycle = (pulse_duration / 2000) * 100  # Cálculo do ciclo de trabalho em porcentagem
    # for _ in range(400):
        # GPIO.output(SERVO_PIN, GPIO.HIGH)
        # time.sleep(duty_cycle * DutyCycleS / 100)
        # GPIO.output(SERVO_PIN, GPIO.LOW)
        # time.sleep((100 - duty_cycle) / 100 * DutyCycleS)
    time.sleep(2)

# Iniciando a câmera:
# camera = picamera.PiCamera()

# Definir as configurações da câmera:
# camera.resolution = (640, 480)  # Resolução da imagem
# camera.rotation = 180           # Rotação da imagem (0, 90, 180 ou 270)

# Definindo os estados e transições:
states = [
    "PosIni",
    "RecepDados",
    "MovX",
    "MovY",
    "Conf",
    "MovCarro",
    "FechGar",
    "MovCarroInit",
    "MovXInit",
    "MovYInit",
    "MovCarro2",
    "AbrGar",
    "MovCarroInit2",
]

transitions = [
    {"trigger": "A", "source": "PosIni", "dest": "MovX"},
    {"trigger": "B", "source": "RecepDados", "dest": "PosIni"},
    {"trigger": "C", "source": "RecepDados", "dest": "MovX"},
    {"trigger": "D", "source": "MovX", "dest": "MovY"},
    {"trigger": "E", "source": "MovY", "dest": "Conf"},
    {"trigger": "F", "source": "Conf", "dest": "MovCarro"},
    {"trigger": "G", "source": "MovCarro", "dest": "FechGar"},
    {"trigger": "H", "source": "FechGar", "dest": "MovCarroInit"},
    {"trigger": "I", "source": "MovCarroInit", "dest": "MovXInit"},
    {"trigger": "J", "source": "MovXInit", "dest": "MovYInit"},
    {"trigger": "K", "source": "MovYInit", "dest": "MovCarro2"},
    {"trigger": "L", "source": "MovCarro2", "dest": "AbrGar"},
    {"trigger": "M", "source": "AbrGar", "dest": "MovCarroInit2"},
    {"trigger": "N", "source": "MovCarroInit2", "dest": "RecepDados"},
]


class RoboManipulador(object):
    pass

    def on_enter_PosIni(self):
        # Não queremos inibir os DEMUX
        GPIO.output(INHIBIT_PIN, GPIO.LOW)

        # Desligando Reset e Sleep
        GPIO.output(GPIO16, GPIO.HIGH)  # Sleep e Reset são invertidos, então desligo com 1 e ligo com 0.

        # Selecionando o eixc Y: CBA = 010
        GPIO.output(A_PIN, GPIO.HIGH)
        GPIO.output(B_PIN, GPIO.LOW)
        GPIO.output(C_PIN, GPIO.LOW)

        # Ativar o motor de passo para mover o eixo Y. Mudando a direção para subir.
        GPIO.output(DIR_PIN, GPIO.HIGH)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int(4 * 4750)  # 680 passos

        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(0.5 * DutyCycle)  # Usando o mesmo delay teremos 50% de duty cycle.
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(0.5 * DutyCycle)
        
        logger.info("Aguardando nova lista...")

    def on_exit_PosIni(self):
        logger.info("Iniciando lista de pedidos...")

        # Não queremos inibir os DEMUX
        GPIO.output(INHIBIT_PIN, GPIO.LOW)

        # Desligando Reset e Sleep
        GPIO.output(GPIO16, GPIO.HIGH)  # Sleep e Reset são invertidos, então desligo com 1 e ligo com 0.

        # Selecionando o eixc Y: CBA = 010
        GPIO.output(A_PIN, GPIO.HIGH)
        GPIO.output(B_PIN, GPIO.LOW)
        GPIO.output(C_PIN, GPIO.LOW)

        # Ativar o motor de passo para mover o eixo Y. Mudando a direção para subir.
        GPIO.output(DIR_PIN, GPIO.LOW)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int(4 * 4750)  # 680 passos

        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(0.5 * DutyCycle)  # Usando o mesmo delay teremos 50% de duty cycle.
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(0.5 * DutyCycle)

    def on_enter_RecepDados(self):
        # Habilitando recepçao da informação:
        logger.info("Aguardando novo objeto...")

        # Adicione o código necessário para enviar a mensagem "pronto" para o Kafka
        # producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
        # message = "pronto"
        # producer.produce(KAFKA_TOPIC, value=message)
        # producer.flush()

        # Se a lista terminar retornar à posição inicial:
        # FSM.B()

    def on_exit_RecepDados(self):
        # Desligando Reset e Sleep
        GPIO.output(GPIO16, GPIO.HIGH)  # Sleep e Reset são invertidos, então desligo com 1 e ligo com 0.

        # Não queremos inibir os DEMUX
        GPIO.output(INHIBIT_PIN, GPIO.LOW)

    def on_enter_MovX(self):
        logger.info(f"Movendo eixo X para a coluna {x}...")

        # Salvando x por segurança convertendo posição para distância:
        global x_desej
        x_desej = x * 13.6  # 19.7 é a distância em cm entre as linhas

        # Selecionando o eixc X: CBA = 000
        GPIO.output(A_PIN, GPIO.LOW)
        GPIO.output(B_PIN, GPIO.LOW)
        GPIO.output(C_PIN, GPIO.LOW)

        # Arrumando a resolução de MicroPasso: 111 para Suavisar o movimento pois com a garra vazia não exige torque.
        GPIO.output(MS1_PIN, GPIO.LOW)
        GPIO.output(MS2_PIN, GPIO.LOW)
        GPIO.output(MS3_PIN, GPIO.LOW)

        # Altera a direção do motor de passo para mover o eixo X
        GPIO.output(DIR_PIN, GPIO.LOW)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada:
        # voltas = distância_desejada/(distância/revolução)
        # passos = voltas * passos/volta
        steps = int((x_desej / DISTANCE_PER_REV) * STEPS_PER_REV)  # rev = dist_desej/dist_por_rev)

        # Gerar os pulsos (steps) necessários para mover o motor de passo para eixo X
        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(0.5 * DutyCycle)
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(0.5 * DutyCycle)

        if y is not None:
            FSM.D()

    def on_exit_MovX(self):
        GPIO.output(STEP_PIN, GPIO.LOW)

    def on_enter_MovY(self):
        logger.info(f"Movendo eixo Y para a linha {y}...")

        # Salvando y por segurança convertendo posição para distância:
        global y_desej
        y_desej = y * 4750  # 4750 é o número de passos para uma linha

        # Selecionando o eixc Y: CBA = 010
        GPIO.output(A_PIN, GPIO.HIGH)
        GPIO.output(B_PIN, GPIO.LOW)
        GPIO.output(C_PIN, GPIO.LOW)

        # Ativar o motor de passo para mover o eixo Y
        GPIO.output(DIR_PIN, GPIO.HIGH)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int(y_desej)

        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(
                0.5 * DutyCycle
            )  # Usando o mesmo delay teremos 50% de duty cycle.
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(0.5 * DutyCycle)

        FSM.E()

    def on_exit_MovY(self):
        GPIO.output(STEP_PIN, GPIO.LOW)
        set_servo_angle(Aberto)

    def on_enter_Conf(self):
        logger.info("Confirmando posição objeto...")
        # Colocar o código para receber a informação da câmera:

        if True:  # Se a confirmação indicar ser o objeto certo:
            FSM.F()

    def on_enter_MovCarro(self):
        global z
        z = 8
        logger.info("Movendo braço da garra...")

        # Calcular a distância a ser andada em cm e salvar em z!!
        # Codificar aqui o código da câmera
        

        # Selecionando o eixo Z: CBA = 010
        GPIO.output(A_PIN, GPIO.LOW)
        GPIO.output(B_PIN, GPIO.HIGH)
        GPIO.output(C_PIN, GPIO.LOW)

        # Ativar o motor de passo para mover o eixo Z
        GPIO.output(DIR_PIN, GPIO.LOW)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int((z / DISTANCE_PER_REV) * STEPS_PER_REV)

        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(0.2 * DutyCycle)
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(0.8 * DutyCycle)
        FSM.G()

    def on_exit_MovCarro(self):
        GPIO.output(STEP_PIN, GPIO.LOW)

    def on_enter_FechGar(self):
        logger.info("Pegando objeto...")

        # Selecionando o Servo Motor: CBA = 011
        GPIO.output(A_PIN, GPIO.HIGH)
        GPIO.output(B_PIN, GPIO.HIGH)
        GPIO.output(C_PIN, GPIO.LOW)

        # Controlando a garra para que feche no ângulo desejado:
        set_servo_angle(tamanho)

        FSM.H()

    def on_enter_MovCarroInit(self):
        global z
        z = 8
        logger.info("Retornando braço da garra...")
        
        # Selecionando o eixo Z: CBA = 010
        GPIO.output(A_PIN, GPIO.LOW)
        GPIO.output(B_PIN, GPIO.HIGH)
        GPIO.output(C_PIN, GPIO.LOW)

        # Ativar o motor de passo para mover o eixo Z
        GPIO.output(DIR_PIN, GPIO.HIGH)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int((z / DISTANCE_PER_REV) * STEPS_PER_REV)

        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(0.2 * DutyCycle)
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(0.8 * DutyCycle)

        FSM.I()

    def on_exit_MovCarroInit(self):
        GPIO.output(STEP_PIN, GPIO.LOW)

    def on_enter_MovXInit(self):
        global x_desej
        logger.info("Retornando eixo X para posição de entrega...")
        
        x_desej = x * 13.6  # 19.7 é a distância em cm entre as linhas
        
        # Selecionando o eixc X: CBA = 000
        GPIO.output(A_PIN, GPIO.LOW)
        GPIO.output(B_PIN, GPIO.LOW)
        GPIO.output(C_PIN, GPIO.LOW)

        # Altera a direção do motor de passo para mover o eixo X
        GPIO.output(DIR_PIN, GPIO.HIGH)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int((x_desej / DISTANCE_PER_REV) * STEPS_PER_REV)

        # Gerar os pulsos (steps) necessários para mover o motor de passo para eixo X
        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(DutyCycle)  # Usando o mesmo atraso teremos 50% de duty cycle.
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(DutyCycle)

        FSM.J()

    def on_exit_MovXInit(self):
        GPIO.output(STEP_PIN, GPIO.LOW)

    def on_enter_MovYInit(self):
        logger.info("Retornando eixo Y para posição de entrega...")
        global y_desej
        y_desej = y * 4750
        # Selecionando o eixc Y: CBA = 010
        GPIO.output(A_PIN, GPIO.HIGH)
        GPIO.output(B_PIN, GPIO.LOW)
        GPIO.output(C_PIN, GPIO.LOW)

        # Ativar o motor de passo para mover o eixo Y. Mudando a direção para subir.
        GPIO.output(DIR_PIN, GPIO.LOW)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int(y_desej)

        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(DutyCycle)  # Usando o mesmo delay teremos 50% de duty cycle.
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(DutyCycle)

        FSM.K()

    def on_exit_MovYInit(self):
        GPIO.output(STEP_PIN, GPIO.LOW)

    def on_enter_MovCarro2(self):
        global z
        z = 8
        logger.info("Movendo braço da garra para entrega...")

        # Selecionando o eixo Z: CBA = 010
        GPIO.output(A_PIN, GPIO.LOW)
        GPIO.output(B_PIN, GPIO.HIGH)
        GPIO.output(C_PIN, GPIO.LOW)

        # Ativar o motor de passo para mover o eixo Z
        GPIO.output(DIR_PIN, GPIO.LOW)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int((z / DISTANCE_PER_REV) * STEPS_PER_REV)

        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(0.2 * DutyCycle)
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(0.8 * DutyCycle)

        FSM.L()
        
    def on_exit_MovCarro2(self):
        GPIO.output(STEP_PIN, GPIO.LOW)

    def on_enter_AbrGar(self):
        logger.info("Deixando objeto...")

        # Selecionando o Servo Motor: CBA = 011
        GPIO.output(A_PIN, GPIO.HIGH)
        GPIO.output(B_PIN, GPIO.HIGH)
        GPIO.output(C_PIN, GPIO.LOW)

        # Controlando a garra para que abra:
        set_servo_angle(Aberto)  # Para retornar ao ângulo inicial

        FSM.M()

    #    def on_exit_AbrGar(self):
    #        servo_pwm.stop()

    def on_enter_MovCarroInit2(self):
        global z
        z = 8
        logger.info("Retornando braço da garra...")

        # Selecionando o eixo Z: CBA = 010
        GPIO.output(A_PIN, GPIO.LOW)
        GPIO.output(B_PIN, GPIO.HIGH)
        GPIO.output(C_PIN, GPIO.LOW)

        # Ativar o motor de passo para mover o eixo Z
        GPIO.output(DIR_PIN, GPIO.HIGH)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int((z / DISTANCE_PER_REV) * STEPS_PER_REV)

        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(0.2 * DutyCycle)
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(0.8 * DutyCycle)

        FSM.N()
    
    def on_exit_MovCarroInit2(self):
        GPIO.output(STEP_PIN, GPIO.LOW)
        set_servo_angle(Fechado)

def delivery_report(err, msg):
    if err is not None:
        logger.error("Message delivery failed: {}".format(err))
    else:
        logger.info(
            "Message delivered to {} [{}]".format(msg.topic(), msg.partition())
        )

def encode_message(message):
    return json.dumps(message).encode("utf-8")

FSM = RoboManipulador()

machine = Machine(FSM, states=states, transitions=transitions, initial="PosIni")


try:
    parser = argparse.ArgumentParser(description="This is my robotic arm script.")
    parser.add_argument('-x', metavar='x', type=int, default=None, help='Coordinate X')
    parser.add_argument('-y', metavar='y', type=int, default=None, help='Coordinate Y')
    parser.add_argument('-t', metavar='t', type=str, default=None, help='Size of the box')
    args = parser.parse_args()

    x = args.x
    y = args.y
    tamanho = args.t

    if x and y:
        logger.info(f"Item: tamanho {tamanho}, coords: {x}, {y}")

        if tamanho == "P":
            tamanho = P
        elif tamanho == "M":
            tamanho = M
        elif tamanho == "G":
            tamanho = G

        # if ((x != 0) ) or ((y != 0) and (y != oldy)):
        if FSM.is_PosIni():
            FSM.A()  # Chama o gatilho A para iniciar processo
        elif FSM.is_RecepDados():
            FSM.C()  # Chama o gatilho C para iniciar processo
        
        logger.info("Fim do pedido")
        FSM.B()  # Retorna à posição inicial com o gatilho B
        sys.exit()

    # Configurações do consumidor Kafka
    conf = {
        "bootstrap.servers": "kafka:9092",  # Endereço do servidor Kafka
        "group.id": "motor-consumer",
        "auto.offset.reset": "earliest",
    }

    # Criação do consumidor Kafka
    consumer = Consumer(conf)

    # Tópico a ser consumido
    topic = "order-products"

    # Subscreve ao tópico
    consumer.subscribe([topic])

    producer = Producer({"bootstrap.servers": "kafka:9092"})

    while True:
        logger.info("Aguardando mensagem de pedido")

        # Aguarda a chegada de mensagens Kafka
        msg = consumer.poll(1.0)

        if msg is None:
            continue

        if msg.error():
            logger.error(f"Erro ao receber a mensagem: {msg.error()}")
            continue

        if msg is not None:
            logger.info('Pedido recebido')

            msg = json.loads(msg.value())  # Decodifica a mensagem JSON

            product_list_msg = msg.get('message')

            order_id = product_list_msg.get('order_id')

            for data in product_list_msg.get("products"):
                tamanho = data.get("size")  # Obtém o tamanho do objeto
                x = data.get("position_x")  # Obtém o valor de X da coordenada
                y = data.get("position_y")  # Obtém o valor de Y da coordenada


                logger.info(f"Item: tamanho {tamanho}, coords: {x}, {y}")

                if tamanho == "P":
                    tamanho = P
                elif tamanho == "M":
                    tamanho = M
                elif tamanho == "G":
                    tamanho = G

                # if ((x != 0) ) or ((y != 0) and (y != oldy)):
                if FSM.is_PosIni():
                    FSM.A()  # Chama o gatilho A para iniciar processo
                elif FSM.is_RecepDados():
                    FSM.C()  # Chama o gatilho C para iniciar processo
        
            logger.info("Fim do pedido")
            if FSM.is_RecepDados():
                FSM.B()  # Retorna à posição inicial com o gatilho B

            message = {
                'order_id': order_id,
                'status': 'finished'
            }

            producer.produce(
                'order-status',
                encode_message({
                    "timestamp": datetime.now().timestamp(),
                    "sender": 'robotic-arm',
                    "message": message,
                }),
                callback=delivery_report
            )

            producer.flush()

except KeyboardInterrupt:  # Apertando Ctrl+C
    print("Keyboard interrupt")
    #    camera.stop_preview()
    #    camera.close()          # Encerrou a câmera
    #    consumer.close()        # Encerrou o Kafka
    GPIO.cleanup()  # Encerrou as portas


from transitions import Machine, State
from confluent_kafka import Consumer
from RPiMotorLib import A4988Nema
import RPi.GPIO as GPIO
import picamera
import time

# Definindo as portas:
A_PIN       = 26   # Pino para o seletor A
B_PIN       = 20   # Pino para o seletor B
C_PIN       = 19   # Pino para o seletor C
INHIBIT_PIN = 21   # Pino para inibir os DEMUX
DIR_PIN     = 24   # Pino para a direção dos motores de passo
STEP_PIN    = 12   # Pino para o PWM (step) dos motores de passo 
MS1_PIN     = 17   # Pino para a resolução de MicroPasso 1
MS2_PIN     = 27   # Pino para a resolução de MicroPasso 2
MS3_PIN     = 22   # Pino para a resolução de MicroPasso 3

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

# Configurações para o controle do motor de passo
DutyCycle = 0.001  # Delay entre os pulsos (segundos) -> 1ms = 1KHz 
STEPS_PER_REV = 200  # Quantidade de passos para uma rotação completa
DISTANCE_PER_REV = 10.0  # Distância percorrida em uma rotação completa

# Iniciando a câmera: 
camera = picamera.PiCamera()

# Definir as configurações da câmera:
camera.resolution = (640, 480)  # Resolução da imagem
camera.rotation = 180           # Rotação da imagem (0, 90, 180 ou 270)

class RoboManipulador(object):
    pass
    
    states=['RecepDados', 'MovX', 'MovY', 'Conf', 'MovCarro', 'FechGar', 'MovCarroInit', 'MovXInit', 'MovYInit', 'AbrGar', 'Err', 'ConfPos', 'NewX', 'NewY']
    
    transitions = [
    { 'trigger': 'A', 'source': 'RecepDados', 'dest': 'MovX' },
    { 'trigger': 'B', 'source': 'MovX', 'dest': 'MovY' },
    { 'trigger': 'C', 'source': 'MovY', 'dest': 'Conf' },
    { 'trigger': 'D', 'source': 'Conf', 'dest': 'MovCarro' },
    { 'trigger': 'E', 'source': 'MovCarro', 'dest': 'FechGar' },
    { 'trigger': 'F', 'source': 'FechGar', 'dest': 'MovCarroInit' },
    { 'trigger': 'G', 'source': 'MovCarroInit', 'dest': 'MovXInit' },
    { 'trigger': 'H', 'source': 'MovXInit', 'dest': 'MovYInit' },
    { 'trigger': 'I', 'source': 'MovYInit', 'dest': 'AbrGar' },
    { 'trigger': 'J', 'source': 'AbrGar', 'dest': 'Err' },
    { 'trigger': 'K', 'source': 'Err', 'dest': 'ConfPos' },
    { 'trigger': 'L', 'source': 'ConfPos', 'dest': 'NewX' },
    { 'trigger': 'M', 'source': 'NewX', 'dest': 'NewY' },
    { 'trigger': 'N', 'source': 'NewY', 'dest': 'RecepDados' },
    ]
    
    def on_enter_MovX(self, x):
        print("Movendo eixo X...")
        # Ativar o motor de passo para mover o eixo X
        GPIO.output(DIR_PIN, GPIO.HIGH)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        distance = 10  # Distância em centímetros
        steps = int((distance / DISTANCE_PER_REV) * STEPS_PER_REV)

        # Gerar os pulsos (steps) necessários para mover o motor de passo para eixo X
        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(DutyCycle)
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(DutyCycle) 
        
        if y is not None:
            FSM.B(y)

    def on_exit_MovX(self):
        GPIO.output(STEP_PIN, GPIO.LOW)
        # Adicione o código necessário para desativar o motor de passo do eixo X

    def on_enter_MovY(self, y):
        print("Movendo eixo Y...")
        GPIO.output(DIR_PIN, GPIO.HIGH)
        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(DutyCycle) # Usando o mesmo delay teremos 50% de duty cycle.
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(DutyCycle)
            
        FSM.C()
            
    def on_exit_MovY(self):
        GPIO.output(STEP_PIN, GPIO.LOW)
        
    def on_enter_Conf(self)
        print("Confirmando objeto...")
        
    def on_exit_Conf(self)
    
    def on_enter_Conf(self)
        if 
    def on_exit_Conf(self)
    
    def on_enter_MovCarro(self)
    def on_exit_MovCarro(self)
    
    def on_enter_FechGar(self)
    def on_exit_FechGar(self)
    
    def on_enter_MovCarInit(self)
    def on_exit_MovCarInit(self)
    
    def on_enter_MovXInit(self)
    def on_exit_MovXInit(self)
    
    def on_enter_MovYInit(self)
    def on_exit_MovYInit(self)
    
    def on_enter_AbrGar(self)
    def on_exit_AbrGar(self)
    
    def on_enter_Err(self)
    def on_exit_Err(self)
    
    def on_enter_ConfPos(self)
    def on_exit_ConfPos(self)
    
    def on_enter_NewX(self)
    def on_exit_NewX(self)
    
    def on_enter_NewY(self)
    def on_exit_NewY(self)
  
FSM = RoboManipulador()

transitions = [
    { 'trigger': 'A', 'source': 'RecepDados', 'dest': 'MovX' },
    { 'trigger': 'B', 'source': 'MovX', 'dest': 'MovY' },
    { 'trigger': 'C', 'source': 'MovY', 'dest': 'Conf' },
    { 'trigger': 'D', 'source': 'Conf', 'dest': 'MovCarro' },
    { 'trigger': 'E', 'source': 'MovCarro', 'dest': 'FechGar' },
    { 'trigger': 'F', 'source': 'FechGar', 'dest': 'MovCarroInit' },
    { 'trigger': 'G', 'source': 'MovCarroInit', 'dest': 'MovXInit' },
    { 'trigger': 'H', 'source': 'MovXInit', 'dest': 'MovYInit' },
    { 'trigger': 'I', 'source': 'MovYInit', 'dest': 'AbrGar' },
    { 'trigger': 'J', 'source': 'AbrGar', 'dest': 'Err' },
    { 'trigger': 'K', 'source': 'Err', 'dest': 'ConfPos' },
    { 'trigger': 'L', 'source': 'ConfPos', 'dest': 'NewX' },
    { 'trigger': 'M', 'source': 'NewX', 'dest': 'NewY' },
    { 'trigger': 'N', 'source': 'NewY', 'dest': 'RecepDados' },
]

machine = Machine(FSM, states=states, transitions=transitions, initial='RecepDados')

# Configurações do consumidor Kafka
conf = {
    'bootstrap.servers': 'localhost:9092',  # Endereço do servidor Kafka
    'group.id': 'motor-consumer',
    'auto.offset.reset': 'earliest'
}

# Criação do consumidor Kafka
consumer = Consumer(conf)

# Tópico a ser consumido
topic = 'distancia_motor'

# Subscreve ao tópico
consumer.subscribe([topic])

try:
    while True:
        # Aguarda a chegada de mensagens Kafka
        msg = consumer.poll(1.0)

        if msg is None:
            continue

        if msg.error():
            print(f'Erro ao receber a mensagem: {msg.error()}')
            continue 

        if msg is not None:
            data = json.loads(msg.value())  # Decodifica a mensagem JSON
            x = data.get('x')  # Obtém o valor de X da mensagem
            y = data.get('y')  # Obtém o valor de Y da mensagem

        if x is not None:
            FSM.A(x)  # Chama o gatilho A com o valor de X para mover o eixo X

        # Obtém a distância a partir da mensagem recebida
        distancia = float(msg.value().decode('utf-8'))

        # Chama a função para receber a distância do Kafka
        FSM.receive_distance_from_kafka(distancia)

except KeyboardInterrupt:
    camera.stop_preview()
    camera.close()          # Encerrou a câmera
    consumer.close()        # Encerrou o Kafka
    GPIO.cleanup()          # Encerrou as portas


from transitions import Machine, State
from confluent_kafka import Consumer
from RPiMotorLib import A4988Nema
import RPi.GPIO as GPIO
import picamera
import time

# Definição de tamanho das caixas:
# P -> 180 # Angulo para que o servo pegue a caixa Pequena
# M -> 120 # Angulo para que o servo pegue a caixa Média
# G -> 60 # Angulo para que o servo pegue a caixa Grande

# Definindo as portas:
A_PIN       = 19   # Pino para o seletor A
B_PIN       = 20   # Pino para o seletor B
C_PIN       = 26   # Pino para o seletor C
INHIBIT_PIN = 21   # Pino para inibir os DEMUX
ENABLE_PIN  = 23   # Pino para ativação dos Enable dos motores
STEP_PIN    = 12   # Pino para o PWM (step) dos motores de passo e servo motor
DIR_PIN     = 24   # Pino para a direção dos motores de passo
MS1_PIN     = 17   # Pino para a resolução de MicroPasso 1
MS2_PIN     = 27   # Pino para a resolução de MicroPasso 2
MS3_PIN     = 22   # Pino para a resolução de MicroPasso 3
GPIO16      = 16   # Pino para o reset/sleep dos drivers do motor de passo

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

# Selecionando saída do demux: 
# CH 0 -> CBA = 000
# CH 1 -> CBA = 001
# CH 2 -> CBA = 010
# CH 3 -> CBA = 011 -> Apenas no Step para Servo Motor.

# Configurações para o controle do motor de passo
DutyCycle = 0.001  # Delay entre os pulsos (segundos) -> 1ms = 1KHz 
STEPS_PER_REV = 200  # Quantidade de passos para uma rotação completa
DISTANCE_PER_REV = 4  # Distância percorrida em uma rotação completa (cm)

# Criação do objeto PWM
servo_pwm = GPIO.PWM(STEP_PIN, 500)  # Frequência de 50 Hz (20 ms de período)

# Função para posicionar o servo em um ângulo específico
def set_servo_angle(angle):
    pulse_duration = (angle / 45) * 400  # Cálculo da duração do pulso em microssegundos
    duty_cycle = (pulse_duration / 2000) * 100  # Cálculo do ciclo de trabalho em porcentagem
    servo_pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(0.8)  # Aguarda tempo suficiente para o servo atingir a posição


# Iniciando a câmera: 
camera = picamera.PiCamera()

# Definir as configurações da câmera:
camera.resolution = (640, 480)  # Resolução da imagem
camera.rotation = 180           # Rotação da imagem (0, 90, 180 ou 270)

class RoboManipulador(object):
    pass
    
    states=['RecepDados', 'MovX', 'MovY', 'Conf', 'MovCarro', 'FechGar', 'MovCarroInit', 'MovXInit', 'MovYInit', 'AbrGar', 'Err', 'ConfPos', 'NewX', 'NewY', 'AprErr', 'Autent', 'Desbl']
    
    transitions = [
    { 'trigger': 'A',     'source': 'RecepDados', 'dest': 'MovX' },
    { 'trigger': 'B',     'source': 'MovX', 'dest': 'MovY' },
    { 'trigger': 'C',     'source': 'MovY', 'dest': 'Conf' },
    { 'trigger': 'D',     'source': 'Conf', 'dest': 'ConfPos' },
    { 'trigger': 'D_Err', 'source': 'Conf', 'dest': 'Err' },
    { 'trigger': 'E',     'source': 'ConfPos', 'dest': 'AprErr' },
    { 'trigger': 'F',     'source': 'MovCarro', 'dest': 'FechGar' },
    { 'trigger': 'G',     'source': 'FechGar', 'dest': 'MovCarroInit' },
    { 'trigger': 'H',     'source': 'MovCarroInit', 'dest': 'MovXInit' },
    { 'trigger': 'I',     'source': 'MovXInit', 'dest': 'MovYInit' },
    { 'trigger': 'J',     'source': 'MovYInit', 'dest': 'AbrGar' },
    { 'trigger': 'K',     'source': 'AbrGar', 'dest': 'RecepDados' },
    #{ 'trigger': 'L',     'source': 'Autent', 'dest': 'Desbl' },
    #{ 'trigger': 'M',     'source': 'Desbl', 'dest': 'Bloq' },
    #{ 'trigger': 'N',     'source': 'Bloq', 'dest': 'RecepDados' },
    #{ 'trigger': 'N',     'source': 'NewY', 'dest': 'RecepDados' },
    ]
    
    def on_exit_RecepDados(self)
        # Desligando Reset e Sleep 
        GPIO.output(GPIO16, GPIO.HIGH) # Sleep e Reset são invertidos, então desligo com 1 e ligo com 0.
        
        # Não queremos inibir os DEMUX
        GPIO.output(INHIBIT_PIN, GPIO.LOW)
    
    def on_enter_MovX(self, x):
        print("Movendo eixo X...")
        
        # Salvando x por segurança:
        x_desej = x
        
        # Selecionando o eixc X: CBA = 000
        GPIO.output(A_PIN, GPIO.LOW)
        GPIO.output(B_PIN, GPIO.LOW)
        GPIO.output(C_PIN, GPIO.LOW)
        
        # Arrumando a resolução de MicroPasso: 111 para Suavisar o movimento pois com a garra vazia não exige torque.
        GPIO.output(MS1_PIN, GPIO.HIGH)
        GPIO.output(MS2_PIN, GPIO.HIGH)
        GPIO.output(MS3_PIN, GPIO.HIGH)
        
        # Altera a direção do motor de passo para mover o eixo X
        GPIO.output(DIR_PIN, GPIO.HIGH)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int((x_desej / DISTANCE_PER_REV) * STEPS_PER_REV)

        # Gerar os pulsos (steps) necessários para mover o motor de passo para eixo X
        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(DutyCycle) # Usando o mesmo atraso teremos 50% de duty cycle.
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(DutyCycle) 
        
        if y is not None:
            FSM.B(y)

    def on_exit_MovX(self):
        GPIO.output(STEP_PIN, GPIO.LOW)
        # Adicione o código necessário para desativar o motor de passo do eixo X

    def on_enter_MovY(self, y):
        print("Movendo eixo Y...")
        
        # Salvando y por segurança:
        y_desej = y
        
        # Selecionando o eixc Y: CBA = 010
        GPIO.output(A_PIN, GPIO.HIGH)
        GPIO.output(B_PIN, GPIO.LOW)
        GPIO.output(C_PIN, GPIO.LOW)
        
        # Ativar o motor de passo para mover o eixo Y
        GPIO.output(DIR_PIN, GPIO.HIGH)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int((y_desej / DISTANCE_PER_REV) * STEPS_PER_REV)
        
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
        # Colocar o código para receber a informação da câmera:
        
        if: #Se a confirmação indicar ser o objeto certo:
            FSM.D()
        else: 
            FSM.D_Err()
    
    def on_enter_ConfPos(self)
        print("Confirmando posição da garra...")
        
        FSM.E()
    
    def on_enter_MovCarro(self) 
        print("Movendo braço da garra...")
        
        # Calcular a distância a ser andada em cm e salvar em z!!
        # Codificar aqui o código da câmera
        
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
            
        FSM.F()
        
    def on_exit_MovCarro(self):
        GPIO.output(STEP_PIN, GPIO.LOW)
    
    def on_enter_FechGar(self)
        print("Pegando objeto...")
        
        # Selecionando o Servo Motor: CBA = 011
        GPIO.output(A_PIN, GPIO.LOW)
        GPIO.output(B_PIN, GPIO.HIGH)
        GPIO.output(C_PIN, GPIO.HIGH)
        
        # Controlando a garra para que feche em 90º (?)
        set_servo_angle(90)  # 90 graus
        time.sleep(1)
        
        FSM.G()
    
    def on_exit_FechGar(self)
        servo_pwm.stop()
    
    def on_enter_MovCarInit(self)
        print("Retornando braço da garra...")
        
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
            
        FSM.H()
        
    def on_exit_MovCarInit(self)
        GPIO.output(STEP_PIN, GPIO.LOW)
    
    def on_enter_MovXInit(self)
        print("Retornando eixo X...")

        # Selecionando o eixc X: CBA = 000
        GPIO.output(A_PIN, GPIO.LOW)
        GPIO.output(B_PIN, GPIO.LOW)
        GPIO.output(C_PIN, GPIO.LOW)
        
        # Arrumando a resolução de MicroPasso: 111 para aumentar o torque, pois temos um objeto a ser carregado.
        GPIO.output(MS1_PIN, GPIO.LOW)
        GPIO.output(MS2_PIN, GPIO.LOW)
        GPIO.output(MS3_PIN, GPIO.LOW)
        
        # Altera a direção do motor de passo para mover o eixo X
        GPIO.output(DIR_PIN, GPIO.LOW)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int((x_desej / DISTANCE_PER_REV) * STEPS_PER_REV)

        # Gerar os pulsos (steps) necessários para mover o motor de passo para eixo X
        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(DutyCycle) # Usando o mesmo atraso teremos 50% de duty cycle.
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(DutyCycle)
        
        FSM.I()
        
    def on_exit_MovXInit(self)
        GPIO.output(STEP_PIN, GPIO.LOW)
        
    def on_enter_MovYInit(self)
        print("Retornando eixo Y...")
        
        # Selecionando o eixc Y: CBA = 010
        GPIO.output(A_PIN, GPIO.HIGH)
        GPIO.output(B_PIN, GPIO.LOW)
        GPIO.output(C_PIN, GPIO.LOW)
        
        # Ativar o motor de passo para mover o eixo Y
        GPIO.output(DIR_PIN, GPIO.LOW)  # Defina a direção do motor (pode ser LOW ou HIGH)

        # Calcular a quantidade de passos para a distância desejada
        steps = int((y_desej / DISTANCE_PER_REV) * STEPS_PER_REV)
        
        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(DutyCycle) # Usando o mesmo delay teremos 50% de duty cycle.
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(DutyCycle)
            
        FSM.J()
        
    def on_exit_MovYInit(self)
        GPIO.output(STEP_PIN, GPIO.LOW)
        
    def on_enter_AbrGar(self)
        print("Pegando objeto...")
        
        # Selecionando o Servo Motor: CBA = 011
        GPIO.output(A_PIN, GPIO.LOW)
        GPIO.output(B_PIN, GPIO.HIGH)
        GPIO.output(C_PIN, GPIO.HIGH)
        
        # Controlando a garra para que feche em 90º (?)
        set_servo_angle(90)  # 90 graus
        time.sleep(1)
        
        FSM.K()
        
    def on_exit_AbrGar(self)
        servo_pwm.stop()
        
    def on_enter_Err(self)
        print("Objeto indesejado na posição...")
    def on_exit_Err(self)
    
    def on_enter_NewX(self)
    def on_exit_NewX(self)
    
    def on_enter_NewY(self)
    def on_exit_NewY(self)
  
FSM = RoboManipulador()

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

        if (x!=0) or (y!=0):
            FSM.A(x)  # Chama o gatilho A com o valor de X para mover o eixo X

#        # Obtém a distância a partir da mensagem recebida
#        distancia = float(msg.value().decode('utf-8'))
#
#        # Chama a função para receber a distância do Kafka
#        FSM.receive_distance_from_kafka(distancia)

except KeyboardInterrupt:
    camera.stop_preview()
    camera.close()          # Encerrou a câmera
    consumer.close()        # Encerrou o Kafka
    GPIO.cleanup()          # Encerrou as portas

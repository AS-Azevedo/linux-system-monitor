import shutil
import time

def read_cpu_counters():
    with open('/proc/stat') as arquivo:
        linha = arquivo.readline()  # Pega a primeira linha do arquivo /proc/stat, que contém informações sobre o uso da CPU
        valores_cpu = linha.split()[1:9]  # Pega os valores de uso da CPU (user, nice, system, idle, iowait, irq, softirq, steal) da linha lida e armazena na lista valores_cpu usando slicing (linha.split()[1:9])
        valores_cpu = [int(valor) for valor in valores_cpu]  # Converte os valores de uso da CPU para inteiros usando uma list comprehension e armazena na lista valores_cpu
        total_cpu= sum(valores_cpu)  # Soma os tempos acumulados dos estados da CPU
        idle_cpu= valores_cpu[3] + valores_cpu[4]  # Calcula o tempo de inatividade da CPU somando os valores de idle e iowait (índices 3 e 4 da lista valores_cpu) e armazena na variável idle_cpu
    return total_cpu, idle_cpu

def uptime():
    with open('/proc/uptime') as f:
        info_uptime = f.read()
        info_uptime = info_uptime.split()
        uptime_seconds = float(info_uptime[0])
        uptime_hours = int(uptime_seconds // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
    return uptime_hours, uptime_minutes

def memory_usage():
    with open('/proc/meminfo') as arquivo:
        for linha in arquivo:
            if linha.startswith('MemTotal'):
                mem_total = int(linha.split()[1])
                mem_total = mem_total / 1024 / 1024 #em GiB
            elif linha.startswith('MemAvailable'):
                mem_available = int(linha.split()[1])
                mem_available = mem_available / 1024 / 1024 #em GiB
    return mem_total, mem_available

def disk_usage():
    armazenamento = shutil.disk_usage("/")
    disk_total = armazenamento.total / (1024 ** 3)  # Convertendo para GiB
    disk_used = armazenamento.used / (1024 ** 3)    # Convertendo para GiB
    disk = round((disk_used / disk_total) * 100, 2)  # Calculando
    return disk_total, disk_used, disk

nome = 'LINUX SYSTEM MONITOR'
while True:
    # disk
    disk_total, disk_used, disk = disk_usage()

    # uptime 
    uptime_hours, uptime_minutes = uptime()
    # memory
    mem_total, mem_available = memory_usage()

    total_cpu, idle_cpu = read_cpu_counters()  # Lê o uso da CPU no primeiro instante
    time.sleep(1)  # Espera 1 segundo
    total_cpu_2, idle_cpu_2 = read_cpu_counters()  # Lê o uso da CPU no segundo instante após 1 segundo de espera

    delta_total_cpu = total_cpu_2 - total_cpu # Calcula a diferença entre o total de uso da CPU no segundo instante e o total de uso da CPU no primeiro instante e armazena na variável delta_total_cpu
    delta_idle_cpu = idle_cpu_2 - idle_cpu # Calcula a diferença entre o tempo de inatividade da CPU no segundo instante e o tempo de inatividade da CPU no primeiro instante e

    cpu = round((1 - delta_idle_cpu / delta_total_cpu) * 100, 2) # Calcula a porcentagem de uso da CPU usando a fórmula: (1 - delta_idle_cpu / delta_total_cpu) * 100 e o resultado é arredondado para 2 casas decimais usando a função round() que recebe dois argumentos: o valor a ser arredondado e o número de casas decimais desejado
    # calcula a porcentagem de memória usada usando a fórmula: (mem_total - mem_available) / mem_total * 100 e o resultado é arredondado para 2 casas decimais usando a função round() que recebe dois argumentos: o valor a ser arredondado e o número de casas decimais desejado
    ram = round((mem_total - mem_available) / mem_total * 100, 2)


    print('\033[H\033[J', end='')  # Limpa a tela do terminal usando códigos de escape ANSI
    print('-----------------------------')
    print(nome)
    print(f'CPU: {cpu}%')
    print(f'RAM: {ram}%')
    print(f'Disk: {disk}%')
    print(f'Uptime: {uptime_hours} hours, {uptime_minutes} minutes')
    print(f'MemTotal: {round(mem_total, 2)} GiB')
    print(f'MemAvailable: {round(mem_available, 2)} GiB')

    print('-----------------------------')
    print('Press Ctrl+C to exit')
    print('-----------------------------')
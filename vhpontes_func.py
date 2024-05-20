
def machine_precision():
    #Precisão da Máquina Algoritmo
    u = 1.0
    while 1.0 + u != 1.0:
        u = 0.5*u
    u = 2*u
    return u

def my_sqrt(value: float, precision: float = None, max_iterations: int = 1_000) -> float:
    """
    Calculate the square root of a given number using the Newton-Raphson method.

    Parameters:
    - value (float): The number to find the square root of. Must be non-negative.
    - precision (float): The precision of the result. Default is 0.0001.
    - max_iterations (int): The maximum number of iterations to perform. Default is 10,000.

    Returns:
    - float: The approximated square root of the given number.

    Raises:
    - ValueError: If `value` is negative.
    """
    if precision is None:
        precision = machine_precision()

    if value < 0:
        raise ValueError("Cannot compute the square root of a negative number.")

    if value == 0:
        return 0

    estimate = 1
    for _ in range(max_iterations):
        next_estimate = (estimate + value / estimate) / 2
        if abs(next_estimate - estimate) < precision:
            break
        estimate = next_estimate

    return estimate

def collatz(n):
    count = 0
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        count += 1
    return count

#Funções do cap 3

def encontra_extremos(f, a, b, N=1e6, max_refinements=10, thresh=1e-15):
    """
    Encontra um intervalo [a', b'] dentro de [a, b] onde f(a') * f(b') <= 0.

    Parameters:
    f (function): Função contínua f(x).
    a (float): Extremidade esquerda do intervalo inicial.
    b (float): Extremidade direita do intervalo inicial.
    N (int, optional): Número de subdivisões do intervalo. Default é 1e6.
    max_refinements (int, optional): Número máximo de refinamentos do intervalo. Default é 10.
    thresh (float, optional): Limite mínimo para dx no refinamento. Default é 1e-15.

    Returns:
    tuple: Intervalo [a', b'] onde f(a') * f(b') <= 0.

    Raises:
    ValueError: Se não for possível encontrar um intervalo onde f(a') * f(b') <= 0.
    """
    def refine_interval(f, a, b, dx):
        x1, x2 = a, a + dx
        while x2 <= b:
            if f(x1) * f(x2) <= 0:
                return x1, x2
            x1, x2 = x2, x2 + dx
        raise ValueError("Não foi possível encontrar um intervalo [a, b] onde f(a) * f(b) <= 0")

    dx = (b - a) / N
    for refinement in range(max_refinements):
        try:
            print(f"Refinamento {refinement + 1}/{max_refinements}: dx = {dx}")
            a, b = refine_interval(f, a, b, dx)
            print(f"Intervalo encontrado: [{a}, {b}]")
            return a, b
        except ValueError:
            dx /= 10
            if dx <= thresh:
                raise ValueError("Não foi possível encontrar um intervalo [a, b] onde f(a) * f(b) <= 0 após refinamentos")
            print(f"Refinamento necessário, novo dx = {dx}")

    raise ValueError("Não foi possível encontrar um intervalo [a, b] onde f(a) * f(b) <= 0 após refinamentos")

def bissect(f, a, b, tol=0.5e-6, max_iter=100):
    """
    Método da bisseção para encontrar a raiz de f(x) no intervalo [a, b].

    Parameters:
    f (function): Função contínua f(x).
    a (float): Extremidade esquerda do intervalo inicial.
    b (float): Extremidade direita do intervalo inicial.
    tol (float, optional): Tolerância para o critério de parada. Default é 0.5e-6.
    max_iter (int, optional): Número máximo de iterações. Default é 100.

    Returns:
    dict: Contém a raiz 'x0' encontrada e o número de iterações 'n'.
    """
    # Função para calcular logaritmo na base 2 usando apenas operações básicas
    def log2(x):
        count = 0
        while x > 1:
            x /= 2
            count += 1
        return count

    # Função para arredondar para cima usando apenas operações básicas
    def ceil(x):
        if int(x) == x:
            return int(x)
        else:
            return int(x) + 1

    # Calcular o número esperado de iterações
    n_expected = ceil(log2((b - a) / tol))

    # Garantir que não exceda o número máximo de iterações
    n_expected = min(n_expected, max_iter)

    for n in range(1, n_expected + 1):
        c = (a + b) / 2
        if f(a) * f(c) < 0:
            b = c
        else:
            a = c

        if abs(b - a) < tol:
            break

    return {'x0': (a + b) / 2, 'n': n}

def falsa_posicao(f, a, b, tol=1e-6, max_iter=100):
    """
    Método da falsa posição para encontrar a raiz de f(x) no intervalo [a, b].

    Parameters:
    f (function): Função contínua f(x).
    a (float): Extremidade esquerda do intervalo inicial.
    b (float): Extremidade direita do intervalo inicial.
    tol (float, optional): Tolerância para o critério de parada. Default é 1e-6.
    max_iter (int, optional): Número máximo de iterações. Default é 100.

    Returns:
    dict: Contém as listas de valores 'a', 'b', 'c' e 'f(x)' para cada iteração.
    """
    a_ = [a]
    b_ = [b]
    c_ = [0]
    F = [0]

    for n in range(max_iter + 1):
        c = (a_[-1] * f(b_[-1]) - b_[-1] * f(a_[-1])) / (f(b_[-1]) - f(a_[-1]))
        c_.append(c)
        F.append(f(c))
        if f(a_[-1]) * f(c_[-1]) > 0:
            a_.append(c)
            b_.append(b)
        else:
            a_.append(a)
            b_.append(c)

        if abs(f(c_[-1])) < tol:
            break

    return {'a': a_, 'b': b_, 'c': c_, 'f(x)': F}


def iteracao_f(f, x0, tol=1e-6, max_iter=100):
    """
    Método de iteração funcional para encontrar a raiz de f(x) a partir de x0.

    Parameters:
    f (function): Função contínua f(x).
    x0 (float): Valor inicial para a iteração.
    tol (float, optional): Tolerância para o critério de parada. Default é 1e-6.
    max_iter (int, optional): Número máximo de iterações. Default é 100.

    Returns:
    dict: Contém a lista de valores 'x_' gerados em cada iteração, o valor final 'x' e o número de iterações 'n'.
    """
    x = [x0]
    for n in range(max_iter):
        x_new = f(x[-1])
        if abs(x_new - x[-1]) < tol:
            break
        x.append(x_new)
    return {'x_': x, 'x': x[-1], 'n': n}

def Deriva(f, x0, epsilon=None):
    """
    Calcula a derivada numérica de f(x) em x0 usando o método da diferença finita.

    Parameters:
    f (function): Função contínua f(x).
    x0 (float): Ponto onde a derivada será calculada.
    epsilon (float, optional): Pequena variação para a diferença finita. Se None, será calculada automaticamente.

    Returns:
    float: Aproximação da derivada de f em x0.
    """
    if epsilon is None:
        epsilon = 1.0
        while 1.0 + epsilon != 1.0:
            epsilon *= 0.5
        epsilon = 10**6 * epsilon  # 2 * epsilon é o zero da máquina

    return (f(x0 + epsilon) - f(x0)) / epsilon


def Newton(f, x0, tol=0.5e-6, max_iter=100, completo=True):
    """
    Método de Newton para encontrar a raiz de f(x) a partir de x0.

    Parameters:
    f (function): Função contínua f(x).
    x0 (float): Valor inicial para a iteração.
    tol (float, optional): Tolerância para o critério de parada. Default é 0.5e-6.
    max_iter (int, optional): Número máximo de iterações. Default é 100.
    completo: Opta por calcular a derivada em todos os passos ou apenas no primeiro

    Returns:
    dict: Contém a lista de valores 'x' gerados em cada iteração, a lista de razões de decremento relativo 'd_r', 
          o número de iterações 'n' e o valor final 'x0'.
    """
    x = [x0]
    d = [1]
    n = 0
    deriv = Deriva(f, x[-1])
    
    while abs(f(x[-1])) > tol and n < max_iter:
        if completo:
            deriv = Deriva(f, x[-1])
        if deriv == 0:
            raise ValueError("Derivada zero encontrada, método de Newton falhou.")
        x_new = x[-1] - f(x[-1]) / deriv
        x.append(x_new)
        d.append(abs(x[-2] - x_new) / abs(x[-2]))
        n += 1
    
    return {'x': x, 'd_r': d, 'n': n, 'x0': x[-1]}





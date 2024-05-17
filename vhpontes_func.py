
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

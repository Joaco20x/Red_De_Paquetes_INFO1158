class ColaArreglo():
    def __init__(self, primero=1, ultimo=0, numElem=0, MAX_ELEM=20):
        self.primero = primero
        self.ultimo = ultimo
        self.numElem = numElem
        self.MAX_ELEM = MAX_ELEM
        self.arreglo = [None] * (self.MAX_ELEM + 1)  # +1 por el índice 0 que no se usa

    def encolar(self, x) -> None:
        if self.numElem < self.MAX_ELEM:
            self.ultimo = (self.ultimo + 1) % (self.MAX_ELEM + 1)
            self.arreglo[self.ultimo] = x
            self.numElem += 1
        else:
            raise OverflowError("Cola llena")
        return None

    def estaVacia(self):
        return self.numElem == 0

    def imprimir(self):
        if self.estaVacia():
            return None
        y = "PRIMERO |"
        for n in range(self.numElem):
            y += f"{self.arreglo[(self.primero + n) % (self.MAX_ELEM + 1)]}|"
        y += "ULTIMO"
        print(y)

    def sacar(self):
        if self.estaVacia():
            return "vacio"
        valor = self.arreglo[self.primero]
        self.arreglo[self.primero] = None
        self.primero = (self.primero + 1) % (self.MAX_ELEM + 1)
        self.numElem -= 1
        return valor

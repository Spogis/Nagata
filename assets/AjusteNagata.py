
    def Nagata(Re):
        a= 30.0
        b = 1.0
        f = 0.1
        alfa = 0.9
        p = 1.0

        Np = a / Re + b * ((10 ** 3 + 0.6 * f * (Re ** alfa)) / (10 ** 3 + 1.6 * f * (Re ** alfa))) ** p

        return Np
    
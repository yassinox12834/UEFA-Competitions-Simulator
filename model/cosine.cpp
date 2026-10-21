#include <iostream>
#include <cmath>
#include <complex>
#include <format>

int main() {
    // Utilisation des nombres complexes car arcsin(60) dépasse l'intervalle [-1, 1]
    std::complex<double> z(60.0, 0.0);
    
    std::complex<double> asin_res = std::asin(z);
    std::complex<double> tan_res  = std::tan(asin_res);
    std::complex<double> cos_res  = std::cos(tan_res);
    
    std::cout << std::format("Résultat complexe : {:.6f} + {:.6f}i\n", 
                             cos_res.real(), cos_res.imag());
    
    return 0;
}

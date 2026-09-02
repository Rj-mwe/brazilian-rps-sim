# 📐 Determinação de Posição do Usuário (Iterative WLS PVT)

---

## 1. Sistema de Equações de Pseudodistância Linearizado
Para cada satélite visível $i = 1, \dots, N$ ($N \ge 4$), a pseudodistância corrigida $\rho_i^*$ relaciona-se com a posição do receptor $\mathbf{x} = [x, y, z]^T$ e com o viés do relógio $b = c \cdot \delta t_{\text{rx}}$:
$$\rho_i^* = \|\mathbf{x}_{\text{sat}, i} - \mathbf{x}\| + b$$

Linearizando em torno de uma posição estimada inicial $\mathbf{x}_0$:
$$\Delta \rho_i = \rho_i^* - (\|\mathbf{x}_{\text{sat}, i} - \mathbf{x}_0\| + b_0)$$
$$\Delta \mathbf{\rho} = G \cdot \Delta \mathbf{x} + \mathbf{\epsilon}$$

onde $G$ é a matriz de cossenos diretores ($N \times 4$):
$$G = \begin{bmatrix}
-\frac{x_{\text{sat},1} - x_0}{R_1} & -\frac{y_{\text{sat},1} - y_0}{R_1} & -\frac{z_{\text{sat},1} - z_0}{R_1} & 1 \\
\vdots & \vdots & \vdots & \vdots \\
-\frac{x_{\text{sat},N} - x_0}{R_N} & -\frac{y_{\text{sat},N} - y_0}{R_N} & -\frac{z_{\text{sat},N} - z_0}{R_N} & 1
\end{bmatrix}$$

---

## 2. Solução por Mínimos Quadrados Ponderados (WLS)
Com matriz de ponderação estocástica $W = \text{diag}(w_1, \dots, w_N)$ baseada na variância do erro de medição $\sigma_i^2 = \frac{\sigma_0^2}{\sin^2(\text{el}_i)}$:
$$\Delta \mathbf{x} = (G^T W G)^{-1} G^T W \Delta \mathbf{\rho}$$

Atualização de estado:
$$\mathbf{x}_{k+1} = \mathbf{x}_k + \Delta \mathbf{x}_{1:3}, \quad b_{k+1} = b_k + \Delta \mathbf{x}_4$$
O processo converge em tipicamente 3 a 5 iterações para $\|\Delta \mathbf{x}\| < 10^{-4}\text{ m}$.

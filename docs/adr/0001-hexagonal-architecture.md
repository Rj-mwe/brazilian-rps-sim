# ADR 0001: Adoção da Arquitetura Hexagonal (Ports & Adapters)

* **Status**: Aprovado e Implementado
* **Data**: 2026-08-25
* **Decisores**: Equipe de Arquitetura e Engenharia de Sistemas RPS-BR

---

## 1. Contexto & Problema
Simulações aeroespaciais frequentemente acoplam a matemática de propagação orbital diretamente aos nós do ROS 2 ou aos plugins C++ do Gazebo. Isso inviabiliza:
1. Testes unitários rápidos e determinísticos sem subir o ecossistema ROS 2.
2. Portabilidade da lógica para plataformas embarcadas ou outros motores (ex: FlightGear, Cesium, STK).
3. Evolução de modelos matemáticos sem introduzir regressões nos drivers de transporte.

---

## 2. Decisão
Adotar estritamente a **Arquitetura Hexagonal (Ports & Adapters)** com **Domain-Driven Design (DDD)**:
* **Domínio Puro (`core/domain/`)**: Contém exclusivamente Value Objects imutáveis (`Vector3DVO`, `KeplerianElementsVO`), entidades, agregados (`ConstellationAggregate`) e serviços matemáticos sem qualquer dependência de `rclpy` ou `gz`.
* **Aplicação (`core/application/`)**: Orquestra os Casos de Uso através de DTOs e define Portas de Saída (`ITelemetryOutboundPort`).
* **Adaptadores (`adapters/`)**: Implementam as portas para tecnologias externas (ex: `Ros2TelemetryOutboundAdapter`).

---

## 3. Consequências & Benefícios
* **Positivas**:
  * 100% dos testes de dinâmica e navegação executam em menos de 1 segundo via `pytest`.
  * Zero vazamento de dependências de infraestrutura para o núcleo físico da missão.
* **Negativas / Desafios**:
  * Exige conversão explícita de tipos (Mappers/DTOs) na fronteira com o ROS 2.

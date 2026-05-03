RoomCopy
O RoomCopy é uma extensão avançada para o G-Earth desenvolvida em Python. Criado especificamente para utilizadores do Clube do Arquiteto, permite a clonagem e colagem de quartos inteiros com precisão absoluta, automatizando processos complexos de construção.

Desenvolvido por Krush.

Descrição
O RoomCopy automatiza a cópia de ambientes, incluindo o mapa de altura do chão, itens de chão, itens de parede e as alturas empilhadas (Z). Um diferencial importante é a sua capacidade de sincronizar os estados (states) dos mobis após a colagem. Agora conta com filtros inteligentes que permitem ignorar itens específicos logo no momento da cópia, garantindo uma prancheta limpa e organizada.

Funcionalidades Principais
Clonagem de Layout: Copia o FloorHeightMap, mobis de chão e mobis de parede.

Filtros: Opções para Não copiar Wireds e Não copiar itens de parede (devido a não precisão), filtrando o conteúdo antes de gerar o preset.

Sincronização de Estados: Garante que mobis interativos (portas, luzes, etc.) fiquem no estado correto após serem colocados.

Gestão de Presets: Exporta e importa quartos em ficheiros .json.

Interface Bilíngue: GUI intuitiva em tkinter com suporte a Português e Inglês.

Furnidata Dinâmica: Atualização automática de dados de mobis via API oficial.

Requisitos
Python 3.x

G-Earth (v1.4.1 ou superior recomendado)

Bibliotecas Python: g-python, requests

Instalação das dependências:
Bash
pip install g-python requests

Como Utilizar
Conectar: Abre o G-Earth e executa o script python roomcopy.py.

Configurar: Na interface, seleciona se desejas ignorar Wireds ou itens de parede antes de iniciar.

Copiar: Dentro do quarto de origem, clica em COPIAR QUARTO.

Colar: * Vai para o quarto de destino.

Clica em COLAR QUARTO. Se o chão for alterado, sai e entra novamente no quarto para validar.

Clica em qualquer lajota (piso) para iniciar o posicionamento dos StackTiles e a colagem automática.

Presets: Utiliza os botões de EXPORTAR e IMPORTAR para gerir os teus ficheiros JSON na pasta presets.

Licença
Este projeto está sob a licença MIT. Consulta o ficheiro LICENSE para mais detalhes.

Aviso: Este script foi desenvolvido para fins educativos e de auxílio em construções. O uso de extensões de terceiros deve ser feito com responsabilidade, respeitando os termos de serviço do jogo.

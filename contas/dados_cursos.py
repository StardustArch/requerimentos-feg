"""Catálogo de cursos da faculdade.

Os nomes não incluem o prefixo do grau: o grau é guardado num campo próprio
do modelo ``Curso``. O mesmo nome pode existir em graus diferentes (por
exemplo, Contabilidade e Auditoria em licenciatura e em mestrado).
"""

CURSOS_LICENCIATURA = [
    "Direito",
    "Contabilidade e Auditoria",
    "Economia e Gestão",
    "Gestão de Recursos Humanos",
    "Administração e Gestão de Empresas",
    "Tecnologias da Informação",
    "Arquitectura",
    "Gestão Portuária",
]

CURSOS_MESTRADO = [
    "Gestão e Administração de Negócios (MBA)",
    "Direito Administrativo",
    "Contabilidade e Auditoria",
    "Gestão de Recursos Humanos",
    "Sistemas de Informação Geográfica e Monitoria dos Recursos Naturais",
    "Economia",
    "Planeamento e Desenvolvimento Regional",
    "Direito Empresarial",
    "Direito Penal",
]

CURSOS_DOUTORAMENTO = [
    "Gestão Empresarial",
]

CURSOS_POR_GRAU = (
    ("licenciatura", CURSOS_LICENCIATURA),
    ("mestrado", CURSOS_MESTRADO),
    ("doutoramento", CURSOS_DOUTORAMENTO),
)

"""
Traduções próprias do Taverna (pt-BR) para partes do SRD 5.1 que não têm tradução no 5e-database.
Tradução livre feita para o Taverna, a partir do SRD 5.1 (CC BY 4.0, Wizards of the Coast).
Distâncias já em metros (5 pés = 1,5 m).
"""

# índice -> (nome, [parágrafos])
TRACOS = {
    "darkvision": ("Visão no Escuro", [
        "Você enxerga muito bem no escuro e na penumbra. Até 18 m de você, enxerga na penumbra "
        "como se fosse luz plena, e no escuro como se fosse penumbra. No escuro você não distingue "
        "cores, só tons de cinza."]),
    "dwarven-resilience": ("Resiliência Anã", [
        "Você tem vantagem em testes de resistência contra veneno e resistência a dano de veneno."]),
    "dwarven-combat-training": ("Treinamento Anão em Combate", [
        "Você tem proficiência com machado de batalha, machadinha, martelo leve e martelo de guerra."]),
    "tool-proficiency": ("Proficiência com Ferramentas", [
        "Você ganha proficiência com uma ferramenta de artesão à sua escolha: ferramentas de ferreiro, "
        "suprimentos de cervejeiro ou ferramentas de pedreiro."]),
    "stonecunning": ("Especialização em Rochas", [
        "Sempre que fizer um teste de Inteligência (História) relacionado à origem de um trabalho em "
        "pedra, você é considerado proficiente em História e soma o dobro do seu bônus de proficiência "
        "ao teste, em vez do bônus normal."]),
    "dwarven-toughness": ("Robustez Anã", [
        "Seu máximo de pontos de vida aumenta em 1, e aumenta mais 1 a cada nível que você ganhar."]),
    "keen-senses": ("Sentidos Aguçados", ["Você tem proficiência na perícia Percepção."]),
    "fey-ancestry": ("Ancestralidade Feérica", [
        "Você tem vantagem em testes de resistência contra ficar enfeitiçado, e magia não pode "
        "colocar você para dormir."]),
    "trance": ("Transe", [
        "Elfos não precisam dormir. Em vez disso, meditam profundamente, semiconscientes, por 4 horas "
        "por dia (no idioma Comum, essa meditação se chama \"transe\"). Enquanto medita, você pode "
        "sonhar de certa forma; esses sonhos são, na verdade, exercícios mentais que se tornaram "
        "reflexos depois de anos de prática. Depois de descansar assim, você recebe o mesmo benefício "
        "que um humano recebe com 8 horas de sono."]),
    "elf-weapon-training": ("Treinamento Élfico com Armas", [
        "Você tem proficiência com espada longa, espada curta, arco curto e arco longo."]),
    "high-elf-cantrip": ("Truque de Alto Elfo", [
        "Você conhece um truque à sua escolha da lista de magias de mago. Inteligência é o seu "
        "atributo de conjuração para ele."]),
    "extra-language": ("Idioma Adicional", [
        "Você sabe falar, ler e escrever um idioma adicional à sua escolha."]),
    "lucky": ("Sortudo", [
        "Quando tirar 1 no d20 numa jogada de ataque, teste de atributo ou teste de resistência, "
        "você pode rolar o dado de novo e deve usar o novo resultado."]),
    "brave": ("Corajoso", ["Você tem vantagem em testes de resistência contra ficar amedrontado."]),
    "halfling-nimbleness": ("Agilidade Halfling", [
        "Você pode se mover pelo espaço de qualquer criatura que seja de um tamanho maior que o seu."]),
    "naturally-stealthy": ("Furtividade Natural", [
        "Você pode tentar se esconder mesmo quando estiver encoberto apenas por uma criatura que seja "
        "pelo menos um tamanho maior que você."]),
    "draconic-ancestry": ("Ancestralidade Dracônica", [
        "Você tem ancestralidade dracônica. Escolha um tipo de dragão da tabela abaixo. O seu sopro "
        "e a sua resistência a dano são determinados pelo tipo de dragão."]),
    "breath-weapon": ("Arma de Sopro", [
        "Você pode usar sua ação para exalar energia destrutiva. Sua ancestralidade dracônica "
        "determina o tamanho, o formato e o tipo de dano do sopro.",
        "Quando usa sua arma de sopro, cada criatura na área precisa fazer um teste de resistência, "
        "do tipo definido pela sua ancestralidade. A CD é 8 + seu modificador de Constituição + seu "
        "bônus de proficiência. A criatura sofre 2d6 de dano se falhar, ou metade se passar. O dano "
        "aumenta para 3d6 no 6º nível, 4d6 no 11º e 5d6 no 16º.",
        "Depois de usar a arma de sopro, você só pode usá-la de novo após um descanso curto ou longo."]),
    "damage-resistance": ("Resistência a Dano", [
        "Você tem resistência ao tipo de dano associado à sua ancestralidade dracônica."]),
    "gnome-cunning": ("Esperteza Gnômica", [
        "Você tem vantagem em todos os testes de resistência de Inteligência, Sabedoria e Carisma "
        "contra magia."]),
    "artificers-lore": ("Conhecimento de Artífice", [
        "Sempre que fizer um teste de Inteligência (História) relacionado a itens mágicos, objetos "
        "alquímicos ou dispositivos tecnológicos, você pode somar o dobro do seu bônus de "
        "proficiência, em vez de qualquer bônus de proficiência que normalmente aplicaria."]),
    "tinker": ("Engenhoqueiro", [
        "Você tem proficiência com ferramentas de artesão (ferramentas de funileiro). Com elas, pode "
        "gastar 1 hora e 10 PO em materiais para construir um pequeno dispositivo mecânico Miúdo "
        "(CA 5, 1 PV). Ele para de funcionar depois de 24 horas (a não ser que você gaste 1 hora "
        "consertando-o para mantê-lo funcionando) ou quando você usa sua ação para desmontá-lo; "
        "nesse momento, você recupera os materiais usados. Você pode ter até três desses "
        "dispositivos funcionando ao mesmo tempo.",
        "Ao criar um dispositivo, escolha uma das opções:",
        "**Brinquedo de corda.** Um animal, monstro ou pessoa de corda, como um sapo, rato, pássaro, "
        "dragão ou soldado. Colocado no chão, ele anda 1,5 m em uma direção aleatória a cada turno "
        "seu, fazendo os barulhos da criatura que representa.",
        "**Acendedor.** Produz uma pequena chama, que você pode usar para acender uma vela, tocha ou "
        "fogueira. Usar o dispositivo exige sua ação.",
        "**Caixinha de música.** Quando aberta, toca uma única música em volume moderado. Para de "
        "tocar quando a música acaba ou quando é fechada."]),
    "skill-versatility": ("Versatilidade em Perícias", [
        "Você ganha proficiência em duas perícias à sua escolha."]),
    "menacing": ("Ameaçador", ["Você ganha proficiência na perícia Intimidação."]),
    "relentless-endurance": ("Resistência Implacável", [
        "Quando seus pontos de vida caem para 0 mas você não morre na hora, pode ficar com 1 ponto de "
        "vida em vez disso. Você só pode usar isso de novo depois de um descanso longo."]),
    "savage-attacks": ("Ataques Selvagens", [
        "Quando acertar um crítico com um ataque corpo a corpo com arma, você pode rolar mais uma vez "
        "um dos dados de dano da arma e somar ao dano extra do crítico."]),
    "hellish-resistance": ("Resistência Infernal", ["Você tem resistência a dano de fogo."]),
    "infernal-legacy": ("Legado Infernal", [
        "Você conhece o truque taumaturgia. Ao chegar ao 3º nível, pode conjurar a magia repreensão "
        "infernal como magia de 2º nível uma vez com este traço, e recupera esse uso após um descanso "
        "longo. Ao chegar ao 5º nível, pode conjurar a magia escuridão uma vez com este traço, e "
        "recupera esse uso após um descanso longo. Carisma é o seu atributo de conjuração para essas "
        "magias."]),
}

# tabela da Ancestralidade Dracônica
ANCESTRALIDADE_DRACONICA = [
    # dragão, tipo de dano, sopro
    ("Azul", "Elétrico", "Linha de 1,5 por 9 m (teste de Des.)"),
    ("Branco", "Frio", "Cone de 4,5 m (teste de Con.)"),
    ("Bronze", "Elétrico", "Linha de 1,5 por 9 m (teste de Des.)"),
    ("Cobre", "Ácido", "Linha de 1,5 por 9 m (teste de Des.)"),
    ("Latão", "Fogo", "Linha de 1,5 por 9 m (teste de Des.)"),
    ("Negro", "Ácido", "Linha de 1,5 por 9 m (teste de Des.)"),
    ("Ouro", "Fogo", "Cone de 4,5 m (teste de Des.)"),
    ("Prata", "Frio", "Cone de 4,5 m (teste de Con.)"),
    ("Verde", "Veneno", "Cone de 4,5 m (teste de Con.)"),
    ("Vermelho", "Fogo", "Cone de 4,5 m (teste de Des.)"),
]

# sub-raças: índice -> (nome, descrição, bônus)
SUBRACAS = {
    "hill-dwarf": ("Anão da Colina",
                   "Como anão da colina, você tem sentidos aguçados, intuição profunda e uma "
                   "resiliência notável.", "SAB +1"),
    "high-elf": ("Alto Elfo",
                 "Como alto elfo, você tem a mente afiada e domina pelo menos o básico da magia. Em "
                 "muitos mundos de fantasia existem dois tipos de altos elfos: um é arrogante e "
                 "recluso, e se acha superior aos não elfos e até aos outros elfos; o outro é mais "
                 "comum e amigável, e costuma ser encontrado entre humanos e outras raças.", "INT +1"),
    "lightfoot-halfling": ("Halfling Pés-Leves",
                           "Como halfling pés-leves, você se esconde com facilidade, usando até outras "
                           "pessoas como cobertura. Costuma ser simpático e se dar bem com os outros. "
                           "Os pés-leves têm mais vontade de viajar que os outros halflings, e muitas "
                           "vezes vivem entre outras raças ou levam uma vida nômade.", "CAR +1"),
    "rock-gnome": ("Gnomo das Rochas",
                   "Como gnomo das rochas, você tem uma inventividade natural e uma resistência "
                   "maiores que as dos outros gnomos.", "CON +1"),
}


# ====================================================================== campos curtos
import re as _re

TEMPO = {"1 action": "1 ação", "1 bonus action": "1 ação bônus", "1 reaction": "1 reação",
         "1 minute": "1 minuto", "10 minutes": "10 minutos", "1 hour": "1 hora", "8 hours": "8 horas",
         "12 hours": "12 horas", "24 hours": "24 horas", "1 round": "1 rodada", "10 days": "10 dias",
         "30 days": "30 dias", "7 days": "7 dias", "2 hours": "2 horas",
         "Instantaneous": "Instantânea", "Special": "Especial", "Until dispelled": "Até ser dissipada",
         "Self": "Pessoal", "Sight": "Visão", "Touch": "Toque", "Unlimited": "Ilimitado",
         "1 mile": "1,5 km", "500 miles": "750 km"}


def tempo(t: str) -> str:
    if not t:
        return ""
    if t.startswith("Up to "):
        return "Até " + TEMPO.get(t[6:], t[6:])
    return TEMPO.get(t, t)


ESCOLAS = {"Abjuration": "Abjuração", "Conjuration": "Conjuração", "Divination": "Adivinhação",
           "Enchantment": "Encantamento", "Evocation": "Evocação", "Illusion": "Ilusão",
           "Necromancy": "Necromancia", "Transmutation": "Transmutação"}

PERICIAS = {"Acrobatics": "Acrobacia", "Arcana": "Arcanismo", "Athletics": "Atletismo",
            "Deception": "Enganação", "History": "História", "Insight": "Intuição",
            "Intimidation": "Intimidação", "Investigation": "Investigação", "Medicine": "Medicina",
            "Nature": "Natureza", "Perception": "Percepção", "Performance": "Atuação",
            "Persuasion": "Persuasão", "Religion": "Religião", "Stealth": "Furtividade",
            "Survival": "Sobrevivência", "Animal Handling": "Adestrar Animais",
            "Sleight of Hand": "Prestidigitação"}
ATRIB = {"STR": "For", "DEX": "Des", "CON": "Con", "INT": "Int", "WIS": "Sab", "CHA": "Car"}


def proficiencia(nome: str) -> str:
    if nome.startswith("Saving Throw: "):
        return "Resistência " + ATRIB.get(nome[14:], nome[14:])
    if nome.startswith("Skill: "):
        return PERICIAS.get(nome[7:], nome[7:])
    return nome


TIPO_CA = {"armor": "armadura", "natural": "armadura natural", "condition": "condição",
           "spell": "magia", "dex": ""}

DANOS = {"acid": "ácido", "bludgeoning": "concussão", "cold": "frio", "fire": "fogo",
         "force": "força", "lightning": "elétrico", "necrotic": "necrótico", "piercing": "perfurante",
         "poison": "veneno", "psychic": "psíquico", "radiant": "radiante", "slashing": "cortante",
         "thunder": "trovejante"}
_DANO_FRASES = [
    ("bludgeoning, piercing, and slashing from nonmagical attacks (from stoneskin)",
     "concussão, perfurante e cortante de ataques não mágicos (por pele de pedra)"),
    ("bludgeoning, piercing, and slashing from nonmagical weapons that aren't adamantine",
     "concussão, perfurante e cortante de armas não mágicas que não sejam de adamante"),
    ("bludgeoning, piercing, and slashing from nonmagical weapons that aren't silvered",
     "concussão, perfurante e cortante de armas não mágicas que não sejam de prata"),
    ("bludgeoning, piercing, and slashing from nonmagical weapons",
     "concussão, perfurante e cortante de armas não mágicas"),
    ("piercing and slashing from nonmagical weapons that aren't adamantine",
     "perfurante e cortante de armas não mágicas que não sejam de adamante"),
    ("piercing from magic weapons wielded by good creatures",
     "perfurante de armas mágicas empunhadas por criaturas boas"),
    ("damage from spells", "dano de magias"),
]


def dano(t: str) -> str:
    for a, b in _DANO_FRASES:
        if t == a:
            return b
    return DANOS.get(t, t)


CONDICOES = {"blinded": "cego", "charmed": "enfeitiçado", "deafened": "surdo",
             "exhaustion": "exaustão", "frightened": "amedrontado", "grappled": "agarrado",
             "incapacitated": "incapacitado", "invisible": "invisível", "paralyzed": "paralisado",
             "petrified": "petrificado", "poisoned": "envenenado", "prone": "caído",
             "restrained": "impedido", "stunned": "atordoado", "unconscious": "inconsciente"}

SUBTIPOS = {"any race": "qualquer raça", "demon": "demônio", "devil": "diabo", "dwarf": "anão",
            "elf": "elfo", "gnome": "gnomo", "goblinoid": "goblinoide", "human": "humano",
            "merfolk": "povo-sereia", "lizardfolk": "povo-lagarto", "orc": "orc",
            "shapechanger": "metamorfo", "titan": "titã"}

TENDENCIAS_EXTRA = {"any alignment": "qualquer tendência", "any chaotic alignment": "qualquer tendência caótica",
                    "any evil alignment": "qualquer tendência maligna",
                    "any non-good alignment": "qualquer tendência não boa",
                    "any non-lawful alignment": "qualquer tendência não leal",
                    "unaligned": "sem tendência",
                    "neutral good (50%) or neutral evil (50%)": "neutro e bom (50%) ou neutro e mau (50%)"}

IDIOMAS = {"Abyssal": "Abissal", "Aquan": "Aquan", "Auran": "Auran", "Celestial": "Celestial",
           "Common": "Comum", "Deep Speech": "Dialeto Subterrâneo", "Draconic": "Dracônico",
           "Druidic": "Druídico", "Dwarvish": "Anão", "Elvish": "Élfico", "Giant": "Gigante",
           "Gnomish": "Gnômico", "Goblin": "Goblin", "Gnoll": "Gnoll", "Ignan": "Ignan",
           "Infernal": "Infernal", "infernal": "Infernal", "Orc": "Orc", "Primordial": "Primordial",
           "Sylvan": "Silvestre", "Terran": "Terran", "Undercommon": "Subcomum",
           "Thieves' cant": "Gíria de Ladrão", "Winter Wolf": "Lobo do Inverno", "Worg": "Worg",
           "Sphinx": "Esfinge", "Blink Dog": "Cão Teleportador", "Giant Eagle": "Águia Gigante",
           "Giant Elk": "Alce Gigante", "Giant Owl": "Coruja Gigante"}
_IDIOMA_FRASES = [
    ("understands all languages it knew in life but can't speak",
     "entende todos os idiomas que conhecia em vida, mas não fala"),
    ("understands all languages it spoke in life but can't speak",
     "entende todos os idiomas que falava em vida, mas não fala"),
    ("understands commands given in any language but can't speak",
     "entende comandos dados em qualquer idioma, mas não fala"),
    ("understands the languages of its creator but can't speak",
     "entende os idiomas do seu criador, mas não fala"),
    ("any languages it knew in life", "quaisquer idiomas que conhecia em vida"),
    ("the languages it knew in life", "os idiomas que conhecia em vida"),
    ("one language known by its creator", "um idioma conhecido pelo seu criador"),
    ("any one language (usually Common)", "um idioma qualquer (normalmente Comum)"),
    ("any one language", "um idioma qualquer"), ("any two languages", "dois idiomas quaisquer"),
    ("any four languages", "quatro idiomas quaisquer"), ("any six languages", "seis idiomas quaisquer"),
    ("plus up to five other languages", "e até cinco outros idiomas"),
    ("plus any two languages", "e dois idiomas quaisquer"),
    ("(can't speak in boar form)", "(não fala na forma de javali)"),
    ("(works only with creatures that understand Abyssal)", "(só funciona com criaturas que entendem Abissal)"),
]


def idiomas(t: str) -> str:
    if not t:
        return "—"
    for a, b in _IDIOMA_FRASES:
        t = t.replace(a, b)
    t = _re.sub(r"understands (.+?) but can't speak( it)?", r"entende \1, mas não fala", t)
    t = t.replace("all, telepathy", "todos, telepatia").replace("telepathy", "telepatia")
    t = _re.sub(r"\band\b", "e", t)
    for a, b in sorted(IDIOMAS.items(), key=lambda x: -len(x[0])):
        t = _re.sub(rf"(?<![\wÀ-ú]){_re.escape(a)}(?![\wÀ-ú])", b, t)
    return t


CATEGORIAS_EQUIP = {"Adventuring Gear": "Equipamento de aventura", "Armor": "Armadura",
                    "Mounts and Vehicles": "Montarias e veículos", "Tools": "Ferramentas",
                    "Weapon": "Arma"}
PROPRIEDADES = {"Ammunition": "Munição", "Finesse": "Acuidade", "Heavy": "Pesada", "Light": "Leve",
                "Loading": "Recarga", "Monk": "Monge", "Reach": "Alcance", "Special": "Especial",
                "Thrown": "Arremesso", "Two-Handed": "Duas mãos", "Versatile": "Versátil"}

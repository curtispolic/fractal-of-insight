from shared import slugify
from datalayer import get_card_img
from cards import LV0, LV1, LV2, LV3, ELEMENTS, SPIRITTYPES, LINEAGE_BREAK
from archetypes import ARCHETYPES

def rank_mat_card(card_o):
    card = card_o["card"]
    if card in LV0:
        return "0"+card
    if card in LV1:
        return "1"+card
    if card in LV2:
        return "2"+card
    if card in LV3:
        return "3"+card
    return card

def lineage(champname):
    return champname.split(",",1)[0]

def fix_case(cardname):
    repls = {
        "'S":"'s",
        "’S":"'s",
        " And ": " and ",
        " At ":" at ",
        " By ": " by ",
        " From ":" from ",
        " In ":" in ",
        " Into ":" into ",
        " Of ": " of ",
        "Mk Iii": "Mk III",
        "Mk Ii": "Mk II",
        " The ":" the ",
        " To ":" to ",
        " With ":" with ",
        "\u2019S": "'s",
    }
    cardname = cardname.title()
    for k,v in repls.items():
        cardname = cardname.replace(k,v)

    return cardname

class Deck:
    def __init__(self, dl):
        self.dl = dl
        self.fix_dl()
        self.find_spirits()
        self.find_champs()
        self.find_elements()
        self.find_archetypes()
        self.count_cards()
        self.cardlist_imgs()

    def find_spirits(self):
        self.spirits = []
        for card_o in self.dl["material"]:
            card = card_o["card"]
            if card in LV0:
                self.spirits.append(card)
    
    def find_champs(self):
        self.champs = []
        raw_lineages = []
        self.is_hybrid = False
        for card_o in self.dl["material"]:
            card = card_o["card"]
            for lv in [LV1,LV2,LV3]:
                if card in lv:
                    existing_lv_champs = set(self.champs) & set(lv)
                    if existing_lv_champs and lineage(card) not in [lineage(c) for c in existing_lv_champs]:
                        self.is_hybrid = True
                    self.champs.append(card)
                    if lv == LV1:
                        raw_lineages.append(card)
                    elif card in LINEAGE_BREAK:
                        raw_lineages.append(card)
        raw_lineages.sort(key=lambda x: rank_mat_card({"card":x}))
        self.lineages = [lineage(c) for c in raw_lineages]

    
    def find_archetypes(self):
        self.archetypes = []
        for archetype, acards in ARCHETYPES.items():
            if acards.get("element"):
                if acards["element"] not in self.els:
                    #print(f"DQ'd from archetype: {acards['element']} not in {self.els}")
                    continue
            cancel = False
            for anticard in acards.get("notmain",[]):
                for card_o in self.dl["main"]:
                    if card_o["card"] == anticard:
                        cancel = True
                        break
            if cancel:
                continue

            for matcard in acards["mats"]:
                for card_o in self.dl["material"]:
                    if card_o["card"] == matcard:
                        self.archetypes.append( archetype )
                        cancel = True
                        break
                if cancel:
                    break
            if archetype in self.archetypes:
                continue

            for maincard in acards["main"]:
                for card_o in self.dl["main"]:
                    if card_o["card"] == maincard:
                        self.archetypes.append( archetype )
                        cancel = True
                        break
                if cancel:
                    break
    
    def find_elements(self):
        # Doesn't include advanced elements or basic-elemental champs
        els = []
        for spirit in self.spirits:
            for element in ELEMENTS:
                if element in spirit:
                    els.append(element)
                    break
        if not els:
            els.append("Norm")
        self.els = els
    
    def fix_dl(self):
        # TODO: handle more cases where card name isn't properly cased
        for card_o in self.dl["main"]:
            card_o["card"] = fix_case(card_o["card"])
        for card_o in self.dl["material"]:
            card_o["card"] = fix_case(card_o["card"])
        for card_o in self.dl["sideboard"]:
            card_o["card"] = fix_case(card_o["card"])
        self.dl["main"].sort(key=lambda x:x["card"])
        self.dl["sideboard"].sort(key=lambda x:x["card"])
        self.dl["material"].sort(key=rank_mat_card)
    
    def count_cards(self):
        n = 0
        for card in self.dl["main"]:
            n += card["quantity"]
        self.main_total = n

        b = 0
        for card in self.dl["sideboard"]:
            b += card["quantity"]
        self.side_total = b

    def cardlist_imgs(self):
        for cat in ("material", "main", "sideboard"):
            for card_o in self.dl[cat]:
                card_o["img"] = get_card_img(card_o["card"])
    
    def __str__(self):
        spiritstr = ""
        if len(self.spirits) < 1:
            spiritstr = "(Spiritless???) "
        elif len(self.spirits) > 1:
            spiritstr = "(Multi-Spirit) "
        else:
            spirit = self.spirits[0]
            for keyword in SPIRITTYPES:
                if keyword in spirit:
                    spiritstr += keyword + " "
            
            spiritstr += "/".join(self.els)

        # Check lineages for Lv3's that are only there to banish
        # lineages = []
        # for champ in self.champs:
        #     if champ in LV3:
        #         lv2_lineages = [lineage(c) for c in self.champs if c in LV2]
        #         # Note: this assumes that there are no 
        #         if lineage(champ) not in lv2_lineages:
        #             #print(f"Deck missing lineage to {champ} - excluding?")
        #             #print(self.dl["material"])
        #             continue
        #     if lineage(champ) not in lineages:
        #         lineages.append(lineage(champ))

        #lineages = set([lineage(c) for c in self.champs])
        if len(self.lineages) == 1:
            champstr = list(self.lineages)[0]
        elif len(self.lineages) > 1:
            self.champs.sort(key=lambda x: rank_mat_card({"card":x}))
            champset = {lineage(c):True for c in self.champs if lineage(c) in self.lineages}
            champstr = "/".join(champset.keys())
        else:
            champstr = ""
        if self.is_hybrid:
            champstr += " Hybrid"

        if not self.archetypes:
            archetypestr = ""
        else:
            archetype_list = []
            for arche in self.archetypes:
                archetype_list.append(ARCHETYPES[arche].get("shortname", arche))
            archetypestr = " ".join(archetype_list)

        return " ".join((spiritstr, archetypestr, champstr)).replace("  "," ")

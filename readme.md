# ČLB 2 Kramerius
Propojení záznamů v člb na data v Krameriovi.

Z pole `773q` se snažíme dostat na naskenovanou stránku v nějaké digitální knihovně.
Např. záznam [001297463](https://vufind.ucl.cas.cz/Record/001297463) má v poli `773q` hodnotu `18:3/4<73`.
Na základě tohoto se chceme dostat na adresu v (třeba) MZK: [c3c946c0-57a0-11e5-9a33-5ef3fc9ae867](https://www.digitalniknihovna.cz/mzk/view/uuid:58c34dd0-579b-11e5-81eb-001018b5eb5c?page=uuid:c3c946c0-57a0-11e5-9a33-5ef3fc9ae867).

# Jak to uděláme
1. Máme seznam periodik v člb a jejich uuid v digitální knihovně
1. Nemáme dostupná data z Krameria, takže je musíme sami sehnat
    - Kramerius každé stránce / číslu / ročníku / periodiku / atd. přiřazuje uuid
    - Cílem je sehnat toto uuid pro konkrétní stránku, na které se vyskytuje článek v záznamu v člb
    - Využíváme krameriovské API
    - Stáhneme si strukturu digitalizovaného dokumentu (abstraktně to reprezentujeme jako stromy)
1. Z marcovských záznamů se pokusíme napárovat pole `773q` na staženou reprezentaci 
1. Samozřejmě vyřešíme všechny nedokonalosti v zadávání dat a upozorníme na chyby (should be easy, right 🤔)

# Problems
## Nekonzistentní číslování _volume_
Např. [001532746](https://vufind.ucl.cas.cz/Record/001532746) má 773q `2:4<156`, ale v Krameriovi je to volume vedené jako `2 (29)`

Bohužel je i v tomhle člb nekonzistentní.
Např. [001525270](https://vufind.ucl.cas.cz/Record/001525270) má 773q `1 [28]:4<231`, ale další záznam ze stejného periodika [001532741](https://vufind.ucl.cas.cz/Record/001532741) má `2:3<99`.


### Stav
🔴
Asi je třeba změnit podobu záznamu v Krameriovi. Třeba to prohnat funkcí, která odstraní všechno v závorkách. Je otázka, jestli to nerozbije cesty.

Nebo to zkusit namatchovat regexem a nic neměnit (asi je lepší nic neměnit).


## Pomalé stahování
I když používáme API, tak je stahování šíleně pomalé.
A protože je i docela nespolehlivé, tak pro větší periodika často ani nedoběhne do konce.

### Stav
🔴/🟢
Částečné stahování je implementované.
Zbývá zjistit, jak spolehlivě bude fungovat. 🧐

Zkouším implementovat jakousi online verzi, tj. podívám se pouze na stránky, které mají záznamy v člb a ty se pokusím stáhnout.


Taky by šlo projet marcovské záznamy před stahováním z Krameria.
Pokud jsou v nich hezké záznamy (asi skutečně aby 773q bylo: `vol:issue<page` a všechny složky byly rozumné (neobsahovaly závorky, mezery atd.)), tak stáhnout z Krameria jen to nezbytně nutné. 
Tím odpadá potřeba implementovat nějaké heuristiky ještě před stahováním.
Pokud bychom našli nějaké nestandardní 773q, tak bychom stáhli všechno.

Jiná možnost by byla implementovat podporu částečného stahování.


## Špatné údaje v 773q
Zkusit zparsovat `773t` a porovnat to s `773q`?
Např. v [000994686](https://vufind.ucl.cas.cz/Record/000994686) je `773q` špatně, ale `t` vypadá dobře.

### Stav
🟢
Viz kontrola 773 od R.

## Slánský obzor
Řekl bych, že je špatně vedený v Krameriovi.
V člb sice sedí název a issn, ale roky vydání jsou úplně jiné.
Periodikum v Krameriovi je z 1. poloviny 20. století a záznamy v člb jsou z 21. století.
Viz třeba [001567998](https://vufind.ucl.cas.cz/Record/001567998#details), [kramerius](https://kramerius5.nkp.cz/periodical/uuid:597d4560-66fb-11de-ad0b-000d606f5dc6).
### Stav
🟢
Od roku 1899 do 1950 vycházel starý Obzor, ten je digitalizovaný (viz [zde](https://aleph.nkp.cz/F/B7K38VJXJXBXIRI7PTE6JPB8C4CU8VP1QGICNVS7XS6DE2KR8G-28094?func=full-set-set&set_number=084828&set_entry=000002&format=999)).
V člb ale máme spíš novější vydání (od roku 1994).
Takže správná odpověď je 

## Progress bar
🟢
Jednoduchý progress bar sleduje stažené volumes.

Detailnější asi nemá smysl implementovat.
Musel bych vědět, kolik uzlů je z Krameria potřeba stáhnout, takže se musím na všechny zeptat.
To je ale stejně práce jako stahování z Krameria.
Takže sesbírání podkladů pro progress bar zabere stejně času jako stažení samotné.

## Nekonzistentní číslování _issue_
Když je více čísel v ročníku, vše je ok.

Ale může se stát, že záznam v člb neobsahuje issue (třeba `5<6`). 
To se stává, když je pouze jedno issue v celém volume.

### Stav 
🟢
Vyřešené tak, že pokud nenajdu stránku a volume má pouze jedno dítě (v datech z Krameria), tak zkusím číslo tohoto dítěte doplnit do cesty a najít ji znova.

# Roadmap
- Napárování periodik z člb na ta správná v digitálních knihovnách.
    - Stačí pro periodikum v člb najít uuid ve správné knihovně
    - Můžou být problémy s issn a názvy, asi to bude chtít nějakou ruční kontrolu
    - ~~Rok vydání v poli `008` je na pozici `[7:11]`~~
    - [fuzzysearch](https://pypi.org/project/fuzzysearch/)
- Zrychlení stahování dat Krameria
    - Bylo by fajn zkoušet najít pouze stránky, které jsou v záznamech v člb, místo stahování celého Krameria
        - To mi přijde jako takové celkově míň spolehlivé řešení, daleko robustnější je prostě mít všechno
    - ~~Asi lepší nápad je implementovat podporu částečného stahování~~ **hotovo**
    - ~~Jejich API je nespolehlivé a občas se prostě odmlčí~~ **docela dobře řeší použití** `requests.Session()`
- Jak kontrolovat výsledné odkazy? Může se stát
    1) Odkaz vede na správnou stránku a správný článek
    1) Odkaz vede na správnou stránku, ale špatný článek (záznam v člb je špatně)
        - *Musí zkontrolovat člověk.*
    1) Cestu ke stránce není
        - V člb je zapsaná neexistující cesta
        - Stránka není vůbec digitalizovaná 
        - *Dokážeme nějak poznat, která z těchto dvou chyb nastala?*
    - Zkusit implementovat nějaké heuristiky, které by mohly napovědět, co se asi stalo
    - Dát dohromady záznamy, ke kterým jsme nenašli cestu v Krameriovi a ty nějak projet a u každého říct, k čemu asi došlo
        1. Není vůbec digitalizované
        1. `773q` je špatně zadané
        1. `773q` je nějak nestandardní
        1. ... další ...
    - Kromě toho kontrolovat i úspěšně přiřazené záznamy (false positives -- správná forma neznamená správný obsah)
    - Zkontrolovat mnou vytvořené linky s již existujícími
- Pátá verze Krameria
    - Je oproti sedmé poněkud nekonzistentní
- Další knihovny
    - Zatím především MZK (V7) a NKP (V5)
    - Rozumně vypadá i knihovna akademie věd
    - Novější periodika nesledují stránku, ale `article` - takže vyřešit, jak hledat články a ne stránky (např. [002973863](https://vufind.ucl.cas.cz/Record/002973863))

# Etc
- issue = číslo
- volume = ročník
- unit = volume / issue / page
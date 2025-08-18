# Problems
## Nekonzistentní číslování _issue_
### Popis
Když je více čísel v ročníku, vše je ok.

Ale může se stát, že záznam v člb neobsahuje issue (třeba `5<6`). 
To se stává, když je pouze jedno issue v celém volume.

Našel jsem 56 391 záznamů, které nemají uvedené issue (tj. styl 1<100) (tj. zhruba 8.5 %) (`cat all_marc.csv | grep ':' -v | wc -l`)
Např. 001738573.

### Stav 
🟢
Vyřešené tak, že pokud nenajdu stránku a volume má pouze jedno dítě (v datech z Krameria), tak zkusím číslo tohoto dítěte doplnit do cesty a najít ji znova.


## Nekonzistentní číslování _volume_
Např. [001532746](https://vufind.ucl.cas.cz/Record/001532746) má 773q `2:4<156`, ale v Krameriovi je to volume vedené jako `2 (29)`

Bohužel je i v tomhle člb nekonzistentní.
Např. [001525270](https://vufind.ucl.cas.cz/Record/001525270) má 773q `1 [28]:4<231`, ale další záznam ze stejného periodika [001532741](https://vufind.ucl.cas.cz/Record/001532741) má `2:3<99`.


### Stav
🔴
Asi je třeba změnit podobu záznamu v Krameriovi. Třeba to prohnat funkcí, která odstraní všechno v závorkách. Je otázka, jestli to nerozbije cesty.

Nebo to zkusit namatchovat na regexem a nic neměnit (asi je lepší nic neměnit).


## Pomalé stahování
I když používáme API, tak je stahování šíleně pomalé.
A protože je i docela nespolehlivé, tak pro větší periodika často ani nedoběhne do konce.

### Stav
🔴
Zkouším implementovat jakousi online verzi, tj. podívám se pouze na stránky, které mají záznamy v člb a ty se pokusím stáhnout.
Uvidíme, jak to bude fungovat, dost záleží na kvalitě a konzistenci záznamů v člb a Krameriovi.

Jiná možnost by byla implementovat podporu částečného stahování.

## Slánský obzor
Řekl bych, že je špatně vedený v Krameriovi. 
V člb sice sedí název a issn, ale roky vydání jsou úplně jiné. 
Periodikum v Krameriovi je z 1. poloviny 20. století a záznamy v člb jsou z 21. století.
Viz třeba [001567998](https://vufind.ucl.cas.cz/Record/001567998#details), [kramerius](https://kramerius5.nkp.cz/periodical/uuid:597d4560-66fb-11de-ad0b-000d606f5dc6).


# Roadmap
- Napárování periodik z člb na ta správná v digitálních knihovnách.
    - Stačí pro periodikum v člb najít uuid ve správné knihovně
    - Můžou být problémy s issn a názvy, asi to bude chtít nějakou ruční kontrolu
    - [fuzzysearch](https://pypi.org/project/fuzzysearch/)
- Zrychlení stahování dat Krameria
    - Bylo by fajn zkoušet najít pouze stránky, které jsou v záznamech v člb, místo stahování celého Krameria
    - Jejich API je nespolehlivé a občas se prostě odmlčí 
- Jak kontrolovat výsledné odkazy? Může se stát
    1) Odkaz vede na správnou stránku a správný článek
    1) Odkaz vede na správnou stránku, ale špatný článek (záznam v člb je špatně)
        - *Musí zkontrolovat člověk.*
    1) Cestu ke stránce není
        - V člb je zapsaná neexistující cesta
        - Stránka není vůbec digitalizovaná 
        - *Dokážeme nějak poznat, která z těchto dvou chyb nastala?*
- Pátá verze Krameria
    - Je oproti sedmé poněkud nekonzistentní
- Další knihovny
    - Zatím především MZK (V7) a NKP (V5)

# Etc
- issue = číslo
- volume = ročník
- unit = volume / issue / page
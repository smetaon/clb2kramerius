# Problems
## Nekonzistentní číslování _issue_
- když je více čísel v ročníku, vše je ok
1. 002288591: 34. ročník má pouze jedno číslo v Krameriovi i v ČLB vedené jako 1-4 (resp. 1/4 v člb)
    - 773q je vedené jako 34:1/4<90
    - z Krameria dostanu cestu 34<90
    - v této chvíli neumím nalinkovat na Krameria, protože při stahování dat z něj automaticky přeskakuje číslo,pokud je v ročníku pouze jedno (tj. z ročníku jde hned na stránku)
    - šlo by asi opravit zásahem do stahování z Krameria (ale bylo by to ještě křehčí)
2. V naprostém protikladu je 002915442: 40. ročník má pouze jedno číslo. V Krameriovi je vedené jako 1, v ČLB vůbec není 
    - 773q je 40<88, úplně bez čísla
    - v současné chvíli funguje

### Stav
Částečně vyřešené (co když mám cestu k issue z Krameria, ale v člb ji nemám? To by se asi nemělo stát...)
Když chybí `issue` v Krameriovi, ale je v člb, podívám se, jestli jsou všechni potomci `volume` stránky (tj. `'model'=='page'`) a pokud ano, zkusím vypustit `issue` z hledané cesty. Viz commit `cf9f5ec9791449ba9b55b77b95c35524396eb253`.

## Nekonzistentní číslování _volume_
- např. 001532746 má 773q `2:4<156`, ale v Krameriovi je to volume vedené jako `2 (29)`
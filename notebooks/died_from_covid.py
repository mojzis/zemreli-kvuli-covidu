# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.9.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
import pandas as pd
import plotly.express as px
import plotly.io as pio

# %% [markdown]
# # Covid zabíjí
# V poslední době se někteří představitelé státu snaží nepochopitelně zlehčovat dopady pandemie na životy lidí v České Republice.  
# Zřejmě v obavě o "image", snaze vyjít vstříc průmyslu a křiklounům kteří nechtějí nosit roušky, hraje vláda **odporný vabank** s lidskými životy, prohrává a ještě o tom lže.
#
# Je nedůstojné, že se místo **citlivého připomenutí** těch kteří padli za oběť pandemii, vede ve veřejném prostoru podivná debata snažící se zbytečně rozlišit "s covidem" a "na covid".
#
# Umřelo mnohem víc lidí než by umřelo normálně, přímým viníkem je vláda a teď se nešťastně snaží to zamluvit. **Umřelo víc lidí** než kolik říká covidová statistika.
#
# Místo jalového hledání jestli náhodou v těch vykázaných "s covidem" není 1 navíc, měla by vláda zjistit, **proč jich tam tisíce chybí.**
#
# ## Data
# Grafy níže vychází z těchto zdrojů:
# - MZČR: [COVID-19: Přehled úmrtí dle hlášení krajských hygienických stanic](https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19) - aktualizováno jednou týdně v neděli
# - Statistický úřad: [Zemřelí podle týdnů a věkových skupin v České republice](https://www.czso.cz/csu/czso/zemreli-podle-tydnu-a-vekovych-skupin-v-ceske-republice) - aktualizováno týdně v úterý, vždy s 5 týdenním zpožděním
#
#
# Více k problematice počítání obětí pandemie si můžete přečíst ve skvělém článku od Petra Koubského - [Je to daleko horší, než Blatný tvrdí. Česko nevykazuje příliš mnoho úmrtí na covid, ale příliš málo](https://denikn.cz/546629/je-to-daleko-horsi-nez-blatny-tvrdi-cesko-nevykazuje-prilis-mnoho-umrti-na-covid-ale-prilis-malo/?ref=tema)

# %%
# a necessary hack for my current jlab 3.0 setup, should go away soon :)
# %config Completer.use_jedi = False

# %%
# download official covid death stats from the ministry of health - updated on a weekly basis
covid_source = 'https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/umrti.csv'
umrti = pd.read_csv(covid_source)
# download official death stats for CZ, updated weekly with a 5 week delay, counts all deceased people
death_source = 'https://www.czso.cz/documents/62353418/138258857/130185-20data012621.csv/1cc32c1d-1fa8-4973-ad98-22ce40180bfa?version=1.1'
celkova = pd.read_csv(death_source)


# %%
# groupby week and week (ignore age groups, yeah could have as well taken the provided summed part :)
souhrn = celkova[(celkova.rok > 2014) & (celkova.tyden > 30) & (celkova.vek_txt != 'celkem')
                ][['tyden','rok','hodnota']].groupby(['tyden','rok'],as_index=False).sum('hodnota')

# cut 'umrti' into same age groups as used in 'celkova'
vek_borders = [0,15,40,65,75,85,1000]
vek_labels = ['0-14','15-39','40-64','65-74','75-84', '85 a více']
umrti['vek_txt'] = pd.cut(umrti.vek, vek_borders, labels=vek_labels)

# %%
# umrti goes by days, add week number so we can compare it
umrti['dat'] = pd.to_datetime(umrti.datum, errors='coerce')
umrti['tyden'] = umrti.dat.dt.isocalendar().week

# groupby so that we can merge with 'celkova'
umrti['hodnota'] = 1
cost = umrti[['tyden','vek_txt','hodnota']].groupby(['tyden','vek_txt'],as_index=False).sum('hodnota')
cost['rok'] = 'covid'

# picking just the most diverging weeks and only recent years
vyber = celkova[['tyden', 'vek_txt','hodnota','rok']
               ][
    (celkova.rok > 2014) & (celkova.tyden > 40) & (celkova.vek_txt != 'celkem')]

# average of the years prior to 2020
prumer = vyber[vyber.rok != 2020][['tyden', 'vek_txt','hodnota']].groupby(['tyden', 'vek_txt'], as_index=False).mean('hodnota')
prumer.hodnota = prumer.hodnota.round()
prumer['rok'] = 'prumer'

# average + covid data
scovidem = prumer.append(cost[cost.tyden > 40])[['tyden', 'vek_txt','hodnota']
                                               ].groupby(['tyden', 'vek_txt'], as_index=False).sum('hodnota')
scovidem['rok'] = 'prumer + covid'

# df to chart 2020, average and average + covid together
spolu = scovidem.append(prumer)
spolu = spolu.append(vyber[vyber.rok == 2020])

# df to chart comparison of years only
souhrn = souhrn.append(prumer[['tyden', 'rok','hodnota']].groupby(['tyden', 'rok'], as_index=False).sum('hodnota'))

# %% [markdown]
# ## Porovnání počtu zesnulých na podzim 2020 a v předchozích letech

# %%
figall = px.line(
    souhrn,
    x='tyden',
    y='hodnota',
    color='rok',
    render_mode='svg',
    template='plotly_white',
)

figall.update_traces(
    patch={
        'line': {'width': 3, 'color': 'red'},
        'mode': 'lines+markers',
        'marker': {'size': 5, 'color': 'navy'}
    },
    selector=lambda x: x['name'] == '2020')

figall.update_traces(
    patch={
        'line': {'width': 1, 'dash': 'dashdot'}
    },
    selector=lambda x: x['name'] != '2020'
)
figall.update_traces(
    patch={
        'line': {'width': 7, 'color': 'crimson', 'dash':'solid'},
        'opacity': 0.3
    },
    selector={'name':'prumer'}
)

figall.update_traces(patch={'name': 'Průměr 15 - 19'}, selector={'name':'prumer'})
figall.update_xaxes(patch={'title': {'text': 'Týden'}})
figall.update_yaxes(patch={'title': {'text': 'Počet zesnulých'}})
figall.update_layout(
        legend_title_text='Rok',
        hovermode='closest',
)
figall

# %% [markdown]
# Od 38. týdne - 14-20. 9. 2020 se začal počet zesnulých prudce odlišovat od přechozích let, největší rozdíl nastal v týdnech 44 a 45 ( mezi 26.10. a 8.11.) - v těchto týdnech umíralo dvakrát tolik lidí než bylo obvyklé v předchozích letech.

# %% [markdown]
# ## Nadúmrtí vs úmrtí vykázaná s covidem podle věkových skupin

# %%
figsp = px.line(
    spolu[(spolu.tyden < 53) & (~spolu.vek_txt.isin(['0-14','15-39']))],
    x='tyden',
    y='hodnota',
    color='rok',
    render_mode='svg',
    facet_col='vek_txt',
    template='plotly_white',
)
figsp.update_layout(
        legend_title_text='Rok',
        hovermode='closest',
)
figsp.update_yaxes(patch={'title': {'text': 'Počet zesnulých'}}, col=1)
figsp.update_xaxes(patch={'title': {'text': 'Týden'}})
figsp

# %% [markdown]
# Zejména u nejvyšších věkových skupin je velký rozdíl mezi celkovým počtem zesnulých a počtem kdy k průměru posledních let přičteme úmrtí evidovaná jako "covidová". To jsou nejspíš lidé kteří zemřeli kvůli covidu ale nebyli testováni - nejspíš umřeli dřív.

# %%
celkem = spolu[spolu.tyden < 52][['vek_txt','rok','hodnota']].groupby(['vek_txt','rok'],as_index=False).sum('hodnota')


# %% [markdown]
# ## Kolik lidí chybí v evidenci

# %%
figcel = px.bar(
    celkem[~celkem.vek_txt.isin(['0-14','15-39'])], 
    x='vek_txt', y='hodnota', color='rok', barmode='group')
figcel.update_layout(
        legend_title_text='Rok',
        hovermode='closest',
)
figcel.update_xaxes(patch={'title': {'text': 'Věková skupina'}})
figcel.update_yaxes(patch={'title': {'text': 'Počet zesnulých'}})
figcel

# %% [markdown]
# Celkově vykázaný počet zesnulých značně převyšuje součet průměru minulých let a úmrtí vykázaných oficiálně jako covidová.  
# Přes **2000** zesnulých ve věkové kategorii 85 a více, kteří chybí v evidenci.

# %%
with open('died_from_covid/ogimg.png','bw') as ogim:
    ogim.write(pio.to_image(
        figall,
        format='png',
        width=1400, 
        height=700,
        engine='kaleido'))


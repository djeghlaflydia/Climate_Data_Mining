# Projet de fouille de données climatiques — Algérie

Une version organisée et reproductible du projet ERA5. Applique les concepts appropriés des cours de données et d'analyse exploratoire, puis le nettoyage, le prétraitement et la réduction des données, la prévision temporelle et le regroupement climatique.

## Commencer ici

1. Décompressez le projet et ouvrez le terminal dans le dossier `Climate_Data_Mining`.
2. Créez un environnement Python et installez les dépendances :

   ```bash
   python -m venv .venv
   # Linux/macOS: source .venv/bin/activate
   # Windows PowerShell: .venv\\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Lancez JupyterLab depuis le dossier du projet :

   ```bash
   jupyter lab
   ```

4. Exécutez les notebooks dans l'ordre `01`, `02`, `03`, `04`, puis `05`. La plupart des notebooks reconstruisent les résultats à partir des données brutes, donc les fichiers `data/raw/` doivent être présents.

## Structure du projet

```text
Climate_Data_Mining/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/                         # ERA5 original et frontières de l'Algérie
│   ├── processed/                   # Résultats reconstruits par les notebooks
│   └── archive/as_received/         # Sorties de la version reçue, conservées pour vérification
├── notebooks/
│   ├── 01_data_inventory_and_mask.ipynb
│   ├── 02_exploratory_data_analysis.ipynb
│   ├── 03_cleaning_preprocessing_reduction.ipynb
│   ├── 04_supervised_month_ahead_forecast.ipynb
│   └── 05_unsupervised_climate_zones.ipynb
├── src/climate_utils.py             # Fonctions communes pour réduire la répétition du code
└── outputs/figures/                 # Emplacement optionnel pour sauvegarder les figures
```

## Les notebooks et ce qu'ils apprennent

- **01 — Inventaire des données et masque géographique :** Types de données, enregistrements et attributs, dimensions NetCDF, unités et dates, frontières de l'Algérie, masque de grille, réduction spatiale 2×2. La sortie réduite est sauvegardée sous `data/processed/era5_algeria_masked_2x2.nc`.
- **02 — Analyse exploratoire des données :** Statistiques de tendance centrale et de dispersion, distributions et valeurs extrêmes, changement de température et saisonnalité, classification en catégories pour illustration, matrice de corrélation et carte thermique. La moyenne régionale est pondérée approximativement par `cos(latitude)` au lieu de donner à chaque cellule un poids surfacique égal.
- **03 — Nettoyage, prétraitement et réduction :** Vérification de la qualité et valeurs manquantes, distinction entre cellules hors limites et données manquantes, conversion des unités, dérivation de la vitesse du vent, documentation des valeurs extrêmes au lieu de supprimer les phénomènes climatiques réels, agrégation spatiale, normalisation et ACP exploratoire.
- **04 — Apprentissage supervisé :** Prévision de référence de la température régionale du mois suivant en utilisant des décalages temporels, comparaison de la persistance saisonnière, Ridge et forêt aléatoire. La division est temporelle, pas aléatoire, avec un écart d'un mois illustratif pour réduire les risques de fuite.
- **05 — Apprentissage non supervisé :** Regroupement des cellules selon leur empreinte climatique mensuelle, normalisation des caractéristiques et ACP pour la visualisation, comparaison de plusieurs nombres de clusters. Les résultats sont exploratoires et ne constituent pas une classification officielle des zones climatiques.

## Données et notes scientifiques

- Le fichier brut est `data/raw/era5_algeria_raw.nc`, et les frontières de l'Algérie sont dans `data/raw/dz.json`.
- Dimensions enregistrées dans la source : 141 pas de temps mensuels de janvier 2015 à septembre 2026, et 191 latitudes × 211 longitudes, avec 12 variables climatiques. Les notebooks vérifient cela lors de l'exécution et ne le supposent pas silencieusement.
- Le masque sélectionne les cellules dont les centres sont à l'intérieur du polygone de l'Algérie selon `contains` strict ; les cellules dont les centres se trouvent sur la frontière sont exclues. Certaines cellules du bord de la grille peuvent être à l'intérieur du polygone mais sans valeurs ERA5, elles sont donc examinées séparément et ne sont pas traitées automatiquement comme des données climatiques manquantes.
- La conversion de la température de Kelvin en Celsius et des précipitations/ruissellement de mètres en millimètres est appliquée uniquement dans la version d'analyse, et ne modifie pas le fichier brut. Les unités des flux d'énergie ne sont pas réinterprétées sans connaître les paramètres de téléchargement et la période d'agrégation dans les données source.
- L'agrégation 2×2 pour réduire la taille de la grille est uniquement pour la visualisation ; les notebooks ne l'utilisent pas automatiquement à la place de la résolution originale pour la prévision.
- La page du cours traitant de ChiMerge était incomplète, donc aucun algorithme ChiMerge non documenté n'a été créé. L'idée du binning apparaît à travers des catégories descriptives claires.
- Les fichiers précédents `era5_algeria_as_received.nc` et `era5_algeria_reduced_4x4_as_received_legacy.nc` sont conservés tels qu'ils ont été reçus dans `data/archive/as_received/`, et ne sont pas des entrées des nouveaux notebooks ; leurs sorties étaient incohérentes avec ce que le code ancien enregistrait. Le fichier 4×4 archivé est conservé uniquement pour vérification ; le chemin actif et ses nouveaux fichiers sont 2×2.

## Note d'évaluation

La prévision ici est un exemple éducatif pour une petite série temporelle régionale, et non un système opérationnel ou une affirmation de prévisions climatiques à long terme. Aucune division aléatoire entre les mois ou les cellules de grille adjacentes n'est utilisée ; cela pourrait fuir des informations temporelles ou spatiales et donner une performance optimiste. Vérifiez également le registre de qualité de la source, les limites des données ERA5, et le type d'agrégation temporelle avant d'interpréter les valeurs comme des moyennes mensuelles ou des totaux mensuels.

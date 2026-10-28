"""Off-premises preprocessing output for the 4 outbreak scenarios (prepared once while online, by an LLM, checked by
the team): decision sheets + translations of the evidence quotes into FR/ES/AR.

On-premises the app only LOOKS UP these strings: no model, no internet. A translation is always shown together with
the original quote, every decision-sheet line points to the quote it comes from, and anything not prepared here is
shown in its original language. Any LLM can regenerate this file (no vendor lock-in).
"""
import re

SHEET_TITLE = {"en": "Decision sheet", "fr": "Fiche de décision", "es": "Ficha de decisión", "ar": "ورقة القرار"}
SHEET_SUB = {"en": "Prepared off-site from the quotes below. Each line points to its source quote.",
             "fr": "Préparée hors site à partir des citations ci-dessous. Chaque ligne renvoie à sa citation source.",
             "es": "Preparada fuera del terreno a partir de las citas de abajo. Cada línea remite a su cita.",
             "ar": "أُعدّت مسبقًا من الاقتباسات أدناه. كل سطر يشير إلى الاقتباس المصدر."}
TRANSLATED = {"fr": "Traduction préparée hors ligne · original :", "es": "Traducción preparada sin conexión · original:",
              "ar": "ترجمة مُعدّة مسبقًا · النص الأصلي:"}
UNTRANSLATED = {"fr": "Langue d'origine : pas de traduction préparée pour cette citation.",
                "es": "Idioma original: no hay traducción preparada para esta cita.",
                "ar": "باللغة الأصلية: لا توجد ترجمة مُعدّة لهذا الاقتباس."}

# scenario -> lines: key (substring of the source quote), then (label, value) per language
SHEETS = {
    "measles": [
        {"key": "85% efficacy", "en": ("Who to vaccinate", "6 months – 15 years"),
         "fr": ("Qui vacciner", "6 mois – 15 ans"), "es": ("A quién vacunar", "6 meses – 15 años"),
         "ar": ("من يجب تطعيمه", "من 6 أشهر إلى 15 سنة")},
        {"key": "85% efficacy", "en": ("Coverage target", "close to 100% (vaccine only 85% effective at 9 months)"),
         "fr": ("Objectif de couverture", "proche de 100 % (vaccin efficace à 85 % à 9 mois)"),
         "es": ("Meta de cobertura", "cercana al 100 % (vacuna eficaz al 85 % a los 9 meses)"),
         "ar": ("هدف التغطية", "قرابة 100% (فعالية اللقاح 85% في عمر 9 أشهر)")},
        {"key": "stubbornly below 50%", "en": ("Watch out", "routine coverage often below 50% in many African countries"),
         "fr": ("Point de vigilance", "couverture de routine souvent sous 50 % dans de nombreux pays africains"),
         "es": ("Atención", "cobertura rutinaria a menudo por debajo del 50 % en muchos países africanos"),
         "ar": ("تنبيه", "التغطية الروتينية غالبًا أقل من 50% في كثير من البلدان الأفريقية")},
    ],
    "cholera": [
        {"key": "MSF has set up cholera treatment centres",
         "en": ("What to set up", "treatment centres + treatment units + oral rehydration points"),
         "fr": ("Quoi mettre en place", "centres et unités de traitement + points de réhydratation orale"),
         "es": ("Qué instalar", "centros y unidades de tratamiento + puntos de rehidratación oral"),
         "ar": ("ما الذي يجب إنشاؤه", "مراكز ووحدات علاج + نقاط إماهة فموية")},
        {"key": "20-bed", "en": ("Size reference", "20-bed unit + 5 oral rehydration points (South Sudan)"),
         "fr": ("Ordre de grandeur", "unité de 20 lits + 5 points de réhydratation (Soudan du Sud)"),
         "es": ("Referencia de tamaño", "unidad de 20 camas + 5 puntos de rehidratación (Sudán del Sur)"),
         "ar": ("مرجع للحجم", "وحدة بـ20 سريرًا + 5 نقاط إماهة (جنوب السودان)")},
        {"key": "389 beds", "en": ("Plan for a surge", "Haiti: 389 beds in 6 centres were often full"),
         "fr": ("Anticiper l'afflux", "Haïti : 389 lits dans 6 centres souvent pleins"),
         "es": ("Prever el aumento", "Haití: 389 camas en 6 centros a menudo llenas"),
         "ar": ("الاستعداد لارتفاع الحالات", "هايتي: 389 سريرًا في 6 مراكز كانت ممتلئة غالبًا")},
    ],
    "ebola": [
        {"key": "Secondary attack rates", "en": ("Contact tracing is a pillar", "secondary attack rate 8–83% (48% with nursing care)"),
         "fr": ("Le suivi des contacts est un pilier", "taux d'attaque secondaire 8–83 % (48 % avec soins infirmiers)"),
         "es": ("El rastreo de contactos es un pilar", "tasa de ataque secundario 8–83 % (48 % con cuidados de enfermería)"),
         "ar": ("تتبع المخالطين ركيزة أساسية", "معدل الهجوم الثانوي 8–83% (48% مع الرعاية التمريضية)")},
        {"key": "Months before the WHO declared",
         "en": ("MSF response package", "patient care, contact tracing, community outreach, logistics"),
         "fr": ("Le dispositif MSF", "soins, suivi des contacts, sensibilisation communautaire, logistique"),
         "es": ("El dispositivo de MSF", "atención, rastreo de contactos, sensibilización comunitaria, logística"),
         "ar": ("حزمة استجابة أطباء بلا حدود", "رعاية المرضى، تتبع المخالطين، التوعية المجتمعية، الدعم اللوجستي")},
        {"key": "monoclonal antibodies",
         "en": ("Protecting contacts (research)", "antibodies after high-risk contact may protect better than vaccinating every contact"),
         "fr": ("Protéger les contacts (recherche)", "des anticorps après un contact à haut risque pourraient mieux protéger que vacciner tous les contacts"),
         "es": ("Proteger a los contactos (investigación)", "los anticuerpos tras un contacto de alto riesgo podrían proteger mejor que vacunar a todos"),
         "ar": ("حماية المخالطين (بحث)", "قد توفر الأجسام المضادة بعد التعرض عالي الخطورة حماية أفضل من تطعيم جميع المخالطين")},
    ],
    "malnutrition": [
        {"key": "combined mortality rate", "en": ("Mortality benchmark", "1.5% achieved; WHO target below 5%"),
         "fr": ("Repère de mortalité", "1,5 % obtenu ; cible OMS sous 5 %"),
         "es": ("Referencia de mortalidad", "1,5 % logrado; meta de la OMS por debajo del 5 %"),
         "ar": ("مرجع الوفيات", "تحقق 1.5%؛ هدف منظمة الصحة العالمية أقل من 5%")},
        {"key": "weight-for-height", "en": ("Screen with MUAC + oedema", "adding them doubles the estimated number of cases"),
         "fr": ("Dépister avec PB + œdèmes", "les inclure double le nombre de cas estimé"),
         "es": ("Cribado con PB + edema", "incluirlos duplica el número estimado de casos"),
         "ar": ("الكشف بمحيط منتصف الذراع والوذمة", "إضافتهما تضاعف العدد المقدّر للحالات")},
        {"key": "hunger season", "en": ("Expect a peak", "malaria season coincides with the hunger season before harvest"),
         "fr": ("Anticiper un pic", "la saison du paludisme coïncide avec la soudure avant la récolte"),
         "es": ("Prever un pico", "la temporada de malaria coincide con la época de hambre antes de la cosecha"),
         "ar": ("توقّع ذروة", "يتزامن موسم الملاريا مع موسم الجوع الذي يسبق الحصاد")},
    ],
}

# evidence quote (identified by its first words) -> translation
QUOTES = {
    "MSF has set up cholera treatment centres": {
        "fr": "MSF a mis en place des centres de traitement du choléra, des unités de traitement du choléra et des points de réhydratation orale dans plusieurs États pour répondre à l'épidémie.",
        "es": "MSF ha instalado centros de tratamiento del cólera, unidades de tratamiento del cólera y puntos de rehidratación oral en varios estados para responder al brote.",
        "ar": "أنشأت أطباء بلا حدود مراكز لعلاج الكوليرا ووحدات لعلاج الكوليرا ونقاطًا للإماهة الفموية في عدة ولايات للاستجابة للتفشي."},
    "Aweil, Northern Bahr-el Ghazal state": {
        "fr": "Aweil, État du Bahr el-Ghazal du Nord — MSF gère une unité de traitement du choléra de 20 lits à Maper West et met actuellement en place cinq points de réhydratation orale dans certaines zones touchées, dont le camp de Wedweil.",
        "es": "Aweil, estado de Bahr el Ghazal del Norte — MSF gestiona una unidad de tratamiento del cólera de 20 camas en Maper West y está instalando cinco puntos de rehidratación oral en algunas de las zonas afectadas, incluido el campo de Wedweil.",
        "ar": "أويل، ولاية شمال بحر الغزال — تدير أطباء بلا حدود وحدة لعلاج الكوليرا بسعة 20 سريرًا في مابر الغربية، وتعمل حاليًا على إنشاء خمس نقاط للإماهة الفموية في بعض المناطق المتضررة، ومنها مخيم ويدويل."},
    "Other humanitarian actors and donors must join": {
        "fr": "Les autres acteurs humanitaires et les bailleurs doivent se joindre à la riposte, soit en ouvrant des centres de traitement, soit en renforçant d'urgence l'accès à l'eau potable et les activités d'assainissement.",
        "es": "Otros actores humanitarios y donantes deben sumarse a la respuesta, ya sea instalando centros de tratamiento o ampliando urgentemente el acceso al agua potable y las actividades de saneamiento.",
        "ar": "يجب على الجهات الإنسانية والمانحين الآخرين الانضمام إلى جهود الاستجابة، إما بإنشاء مراكز علاج أو بتوسيع الوصول إلى المياه الآمنة وأنشطة الصرف الصحي بشكل عاجل."},
    "“Our current centres are filling up": {
        "fr": "« Nos centres actuels se remplissent et nous atteindrons bientôt notre capacité maximale », explique Mumuza Muhindo, directeur pays de MSF en Haïti, à propos des 389 lits souvent pleins dans les six centres de traitement du choléra ouverts par MSF depuis l'apparition des premiers cas le 29 septembre.",
        "es": "«Nuestros centros actuales se están llenando y pronto estaremos al máximo de capacidad», afirma Mumuza Muhindo, director de MSF en Haití, sobre las 389 camas que a menudo están llenas en los seis centros de tratamiento del cólera abiertos por MSF desde los primeros casos del 29 de septiembre.",
        "ar": "«مراكزنا الحالية تمتلئ، وسنصل قريبًا إلى أقصى طاقتنا»، يقول موموزا موهيندو، المدير القطري لأطباء بلا حدود في هايتي، مشيرًا إلى الأسرّة الـ389 الممتلئة غالبًا في مراكز علاج الكوليرا الستة التي أنشأتها المنظمة منذ ظهور الحالات الأولى في 29 سبتمبر."},
    "The use of oral cholera vaccine in outbreak": {
        "fr": "L'utilisation du vaccin oral contre le choléra en situation d'épidémie pourrait aussi être considérablement simplifiée s'il était efficace en une seule dose.",
        "es": "El uso de la vacuna oral contra el cólera en contextos de brote también podría simplificarse considerablemente si fuera eficaz en una sola dosis.",
        "ar": "يمكن أيضًا تبسيط استخدام لقاح الكوليرا الفموي في سياقات التفشي بشكل كبير إذا كان فعالًا بجرعة واحدة."},
    "Given the 85% efficacy of the measles vaccine": {
        "fr": "Compte tenu de l'efficacité de 85 % du vaccin contre la rougeole administré à 9 mois, il faut viser une couverture vaccinale proche de 100 % dans la tranche d'âge de 6 mois à 15 ans.",
        "es": "Dada la eficacia del 85 % de la vacuna contra el sarampión administrada a los 9 meses de edad, es necesario aspirar a una cobertura de vacunación cercana al 100 % en el grupo de edad de 6 meses a 15 años.",
        "ar": "نظرًا لأن فعالية لقاح الحصبة تبلغ 85% عند إعطائه في عمر 9 أشهر، من الضروري السعي إلى تغطية تطعيم تقارب 100% في الفئة العمرية من 6 أشهر إلى 15 سنة."},
    "For more than 10 years recommendations have emphasized": {
        "fr": "Depuis plus de 10 ans, les recommandations insistent sur la nécessité de porter la couverture à plus de 90 % à 9 mois, mais la couverture rougeole reste obstinément inférieure à 50 % dans de nombreux pays africains. Pour ces pays, le bénéfice potentiel d'un schéma précoce à deux doses ou d'un âge de vaccination plus bas mérite d'être étudié.",
        "es": "Desde hace más de 10 años las recomendaciones insisten en aumentar la cobertura a más del 90 % a los 9 meses, pero la cobertura contra el sarampión sigue obstinadamente por debajo del 50 % en muchos países africanos. Para esos países debería estudiarse el posible beneficio de un esquema temprano de dos dosis o de una edad de vacunación más baja.",
        "ar": "منذ أكثر من 10 سنوات تؤكد التوصيات ضرورة رفع التغطية إلى أكثر من 90% في عمر 9 أشهر، لكن تغطية لقاح الحصبة لا تزال دون 50% في كثير من البلدان الأفريقية. وفي هذه البلدان ينبغي دراسة الفائدة المحتملة لجدول مبكر من جرعتين أو لخفض سن التطعيم."},
    "Our results indicate that vaccination coverage": {
        "fr": "Nos résultats indiquent que la couverture vaccinale des enfants actuellement réceptifs devrait augmenter d'au moins 67 % (efficacité vaccinale de 90 %) pour atteindre une couverture de 90 % à l'échelle de la ville.",
        "es": "Nuestros resultados indican que la cobertura de vacunación en los niños actualmente susceptibles debería aumentar al menos un 67 % (eficacia de la vacuna del 90 %) para lograr una cobertura del 90 % en toda la ciudad.",
        "ar": "تشير نتائجنا إلى ضرورة زيادة تغطية التطعيم لدى الأطفال المعرّضين حاليًا للإصابة بنسبة 67% على الأقل (مع فعالية لقاح 90%) للوصول إلى تغطية 90% على مستوى المدينة."},
    "Our results raise the issue of lowering": {
        "fr": "Nos résultats posent la question d'un abaissement de l'âge recommandé pour la vaccination contre la rougeole dans les pays en développement.",
        "es": "Nuestros resultados plantean la cuestión de reducir la edad recomendada para la vacunación contra el sarampión en los países en desarrollo.",
        "ar": "تطرح نتائجنا مسألة خفض السن الموصى به للتطعيم ضد الحصبة في البلدان النامية."},
    "The total vaccination coverage reached after the campaign": {
        "fr": "La couverture vaccinale totale atteinte après la campagne a été estimée à 71,2 % (confirmée par carte de vaccination) par une enquête LQAS (données non publiées d'Epicentre, 2004).",
        "es": "La cobertura total de vacunación alcanzada tras la campaña se estimó en un 71,2 % (confirmada por tarjeta de vacunación) mediante una encuesta LQAS (datos no publicados de Epicentre, 2004).",
        "ar": "قُدّرت تغطية التطعيم الإجمالية بعد الحملة بنسبة 71.2% (مؤكدة ببطاقة التطعيم) عبر مسح بطريقة LQAS (بيانات غير منشورة من إبيسنتر، 2004)."},
    "Secondary attack rates of Ebola virus disease": {
        "fr": "Les taux d'attaque secondaire de la maladie à virus Ebola vont de 8 % à 83 % selon le type de contact (lié à l'exposition virale) et ont été estimés à 48 % lorsque des soins infirmiers sont prodigués. Par conséquent, le suivi des contacts est un pilier important de la riposte aux épidémies d'Ebola.",
        "es": "Las tasas de ataque secundario de la enfermedad por el virus del Ébola oscilan entre el 8 % y el 83 % según el tipo de contacto (relacionado con la exposición viral) y se han estimado en un 48 % cuando se prestan cuidados de enfermería. Por ello, el seguimiento de los contactos es un pilar importante de la respuesta a los brotes de ébola.",
        "ar": "تتراوح معدلات الهجوم الثانوي لمرض فيروس إيبولا بين 8% و83% بحسب نوع المخالطة (المرتبط بالتعرض للفيروس)، وقُدّرت بنحو 48% عند تقديم الرعاية التمريضية. لذلك تُعد متابعة المخالطين ورصدهم ركيزة مهمة في الاستجابة لتفشي إيبولا."},
    "Analyses of health risks related to the job": {
        "fr": "Des mois avant que l'OMS ne déclare l'épidémie d'Ebola urgence de santé publique de portée internationale en août 2014, les équipes de MSF étaient déjà déployées sur plusieurs sites de la région touchée en Afrique de l'Ouest, assurant les soins aux patients, le suivi des contacts, la sensibilisation communautaire et le soutien logistique à la riposte.",
        "es": "Meses antes de que la OMS declarara el brote de ébola emergencia de salud pública de importancia internacional en agosto de 2014, los equipos de MSF ya estaban desplegados en varios lugares de la región afectada de África Occidental, prestando atención a pacientes, rastreo de contactos, sensibilización comunitaria y apoyo logístico a la respuesta.",
        "ar": "قبل أشهر من إعلان منظمة الصحة العالمية تفشي إيبولا حالة طوارئ صحية عامة تثير قلقًا دوليًا في أغسطس 2014، كانت فرق أطباء بلا حدود منتشرة بالفعل في عدة مواقع في منطقة غرب أفريقيا المتضررة، تقدّم رعاية المرضى وتتبع المخالطين والتوعية المجتمعية والدعم اللوجستي للاستجابة."},
    "As WHO has now declared the current Ebola outbreak": {
        "fr": "L'OMS ayant désormais déclaré l'épidémie d'Ebola actuelle en République démocratique du Congo « urgence de santé publique de portée internationale », la riposte mondiale doit aller au-delà des efforts pour augmenter les effectifs et les compétences médicales.",
        "es": "Ahora que la OMS ha declarado el actual brote de ébola en la República Democrática del Congo «emergencia de salud pública de importancia internacional», la respuesta mundial debe ir más allá de los esfuerzos por aumentar el personal y la competencia médica.",
        "ar": "بعد أن أعلنت منظمة الصحة العالمية تفشي إيبولا الحالي في جمهورية الكونغو الديمقراطية «حالة طوارئ صحية عامة تثير قلقًا دوليًا»، يجب أن تتجاوز الاستجابة العالمية جهود زيادة أعداد الكوادر والكفاءة الطبية."},
    "Consequently, we hypothesise that, when used as PEP": {
        "fr": "Nous émettons donc l'hypothèse que, utilisés en prophylaxie post-exposition après un contact à haut risque avec une personne atteinte de la maladie à virus Ebola, les anticorps monoclonaux protègent mieux que la stratégie actuelle consistant à vacciner tous les contacts avec le rVSV-ZEBOV quel que soit leur niveau d'exposition.",
        "es": "Por ello planteamos la hipótesis de que, usados como profilaxis posexposición tras un contacto de alto riesgo con una persona con enfermedad por el virus del Ébola, los anticuerpos monoclonales protegen mejor que la estrategia actual de vacunar a todos los contactos con rVSV-ZEBOV sea cual sea su nivel de exposición.",
        "ar": "لذلك نفترض أن الأجسام المضادة وحيدة النسيلة، عند استخدامها وقايةً بعد التعرض لمخالطة عالية الخطورة مع شخص مصاب بمرض فيروس إيبولا، توفر حماية أفضل من الاستراتيجية الحالية القائمة على تطعيم جميع المخالطين بلقاح rVSV-ZEBOV بغض النظر عن مستوى تعرضهم."},
    "These estimates are based on weight-for-height": {
        "fr": "Ces estimations reposent sur le rapport poids/taille (z-score). Si l'on ajoute les enfants ayant un périmètre brachial (PB) bas et des œdèmes nutritionnels (kwashiorkor), l'estimation de la prévalence double ; si l'on considère l'incidence plutôt que la prévalence, le fardeau augmente fortement. Quels que soient les chiffres exacts, la malnutrition aiguë sévère est une préoccupation majeure.",
        "es": "Estas estimaciones se basan en el puntaje z de peso para la talla. Si se añaden los niños con perímetro braquial (PB) bajo y edema nutricional (kwashiorkor), la prevalencia estimada se duplica; si se considera la incidencia en lugar de la prevalencia, la carga aumenta drásticamente. Sean cuales sean las cifras exactas, la desnutrición aguda severa es una gran preocupación.",
        "ar": "تستند هذه التقديرات إلى مؤشر الوزن مقابل الطول. وإذا أُضيف الأطفال ذوو محيط منتصف الذراع المنخفض والوذمة التغذوية (الكواشيوركور)، يتضاعف تقدير الانتشار؛ وإذا اعتُمد معدل الحدوث بدل الانتشار، يزداد العبء بشكل كبير. وأيًّا كانت الأرقام الدقيقة، يبقى سوء التغذية الحاد الوخيم مصدر قلق كبير."},
    "Overall, the combined mortality rate from severe": {
        "fr": "Globalement, le taux de mortalité combiné de la malnutrition aiguë sévère chez les patients hospitalisés et ambulatoires était de 1,5 % (1 130/77 244), bien en dessous du seuil cible de 5 % recommandé par l'OMS.",
        "es": "En conjunto, la tasa de mortalidad combinada por desnutrición aguda severa en pacientes hospitalizados y ambulatorios fue del 1,5 % (1 130/77 244), muy por debajo del umbral objetivo del 5 % recomendado por la OMS.",
        "ar": "إجمالًا، بلغ معدل الوفيات المشترك لسوء التغذية الحاد الوخيم بين المرضى المقيمين والخارجيين 1.5% (1130 من 77244)، وهو أقل بكثير من العتبة المستهدفة البالغة 5% التي توصي بها منظمة الصحة العالمية."},
    "This peak malaria season often coincides": {
        "fr": "Ce pic de la saison du paludisme coïncide souvent avec la « période de soudure », avant la récolte annuelle, quand les réserves alimentaires des ménages sont limitées et que le risque de malnutrition aiguë chez les jeunes enfants augmente fortement.",
        "es": "Este pico de la temporada de malaria coincide a menudo con la «época de hambre», el periodo previo a la cosecha anual en que las reservas de alimentos de los hogares son limitadas y el riesgo de desnutrición aguda en niños pequeños aumenta considerablemente.",
        "ar": "غالبًا ما تتزامن ذروة موسم الملاريا هذه مع «موسم الجوع»، أي الفترة التي تسبق الحصاد السنوي حين تكون مخزونات الأسر الغذائية محدودة ويزداد خطر سوء التغذية الحاد لدى الأطفال الصغار بشكل كبير."},
    "A novel fortified blended flour, corn-soy blend": {
        "fr": "Une nouvelle farine enrichie, le mélange maïs-soja « plus-plus », n'est pas inférieure aux aliments de supplémentation prêts à l'emploi à base de lipides pour traiter la malnutrition aiguë modérée chez les enfants malawites.",
        "es": "Una nueva harina enriquecida, la mezcla de maíz y soja «plus-plus», no es inferior a los alimentos suplementarios listos para usar a base de lípidos para tratar la desnutrición aguda moderada en niños de Malaui.",
        "ar": "إن دقيقًا مدعّمًا جديدًا، هو خليط الذرة والصويا «بلس بلس»، ليس أقل فعالية من الأغذية التكميلية الجاهزة للاستخدام القائمة على الدهون في علاج سوء التغذية الحاد المتوسط لدى أطفال ملاوي."},
}


def _norm(s):
    return re.sub(r"\s+", " ", s).strip()


def translate(text, lang):
    """Prepared translation of an evidence quote, or None (then the original is shown)."""
    if lang == "en":
        return None
    t = _norm(text)
    for start, tr in QUOTES.items():
        if t.startswith(start):
            return tr.get(lang)
    return None

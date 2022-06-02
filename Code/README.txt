Le script improved_manual_control.py utilise actuellement le module hello
faut de pouvoir compiler et faire fonctionner de nouveau le module data_saving pour
l'enregistrements des données de la caméra évènementielles (le module hello était une
simple ébauche). Mais le module data_saving est sensiblement le même qu'hello, 
je n'ai juste pas eu le temps de trouver pourquoi je ne pouvait plus compiler avec 
le module python cython. 

Il faut regarder les fichiers ".pyx" pour voir le code et le modifier.

Pour améliorer l'enregistrement de données, je vous conseil de regarder les modules
buffered_saver.py et manual_control_buffered_saver.py. Au lieu d'enregistrer
un fichier par frame, ces scripts acumulent les données jusqu'à un certain point
dans un buffer avant d'enregistrer. En combinant cela avec mon multi-threading
sur l'enregistrement des données, vous devriez avoir des résultats drastiquement
meilleurs!
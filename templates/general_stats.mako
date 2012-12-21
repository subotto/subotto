## -*- coding: utf-8 -*-

<table class="statistiche">
<col width="350" />
<col width="180" />

<caption>Statistiche</caption>

<tr>
<td>Differenza reti</td>
<td>${abs(score[0] - score[1])}</td>
</tr>

<tr>
<td>Gol totali</td>
<td>${score[0]+score[1]} (${"%0.2f" % ((score[0]+score[1])/elapsed*60.0)} / min)</td>
</tr>

<tr>
 <td>Parziale</td><td>${partial[0]} - ${partial[1]}</td>
</tr>

<tr><td>Indice di rimonta<br />(gol in pi&ugrave; all'ora che devono segnare i ${teams[1].name} per recuperare i ${teams[0].name})</td><td>${remount_index(score, elapsed, length)}</td></tr>
</table>


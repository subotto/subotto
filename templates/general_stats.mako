## -*- coding: utf-8 -*-

<table>

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

<tr><td>Indice di rimonta<br />(${remount_index_description(score, teams)})</td><td>${remount_index(score, elapsed, length)}</td></tr>
</table>


## -*- coding: utf-8 -*-

<table>

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

<tr>
<td>Punteggio stimato a fine partita</td>
<td>${compute_extimated_score(score, elapsed, length)}</td>
</tr>

<tr>
<%
	target = compute_interesting_score(score[0])
	this_time = compute_linear_projection(score[0], target, elapsed, begin)
%>
<td>Orario stimato per il ${target}-esimo gol<br /> dei ${teams[0].name}</td>
<td>${this_time}</td>
</tr>

<tr>
<%
	target = compute_interesting_score(score[1])
	this_time = compute_linear_projection(score[1], target, elapsed, begin)
%>
<td>Orario stimato per il ${target}-esimo gol<br /> dei ${teams[1].name}</td>
<td>${this_time}</td>
</tr>

</table>


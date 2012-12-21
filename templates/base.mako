## -*- coding: utf-8 -*-

<table class="time">
<tr><td>Tempo trascorso:</td><td>${format_time(int(elapsed))}</td></tr>
<!--<tr><td colspan="2">La partita &egrave; terminata</td></tr></table>-->

<table class="prospetto">
<tr>
 <th>${teams[0].name}</th>
 <th>${teams[1].name}</th>
</tr>

<tr>
 <td>${format_player(players[0][0])}
<br />${format_player(players[0][1])}
</td>
 <td>${format_player(players[1][0])}
<br />${format_player(players[1][1])}
</td>
</tr>

<tr>
 <td>${score[0]}</td>
 <td>${score[1]}</td>
</tr>
</table>


<table class="centro"><tr><td>


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

<br />

<table class="statistiche">

<col width="350" />
<col width="180" />

<caption>Proiezione lineare</caption>

<tr>
<td>Punteggio stimato a fine partita</td>
<td>${int(score[0]*length/elapsed)} - ${int(score[1]*length/elapsed)}</td>
</tr>


<tr>
<%
	target = compute_interesting_score(score[0])
	this_time = compute_linear_projection(score[0], target, elapsed, begin)
%>
<td>Orario	 stimato per il ${target}-esimo gol<br /> dei ${teams[0].name}</td>
<td>${this_time.strftime("%H:%M:%S")}</td>
</tr>

<tr>
<%
	target = compute_interesting_score(score[1])
	this_time = compute_linear_projection(score[1], target, elapsed, begin)
%>
<td>Orario	 stimato per il ${target}-esimo gol<br /> dei ${teams[1].name}</td>
<td>${this_time.strftime("%H:%M:%S")}</td>
</tr>

</table>

</td>

<td>

<br />
<br />

<img src="graph.png" alt="Grafico dei gol" height="500" width="750" />
</td></tr></table>


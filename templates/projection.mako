## -*- coding: utf-8 -*-

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


## -*- coding: utf-8 -*-

<table class="prospetto">
<col width="380" />
<col width="380" />

<tr>
 <th>${teams[0].name}</th>
 <th>${teams[1].name}</th>
</tr>

<tr>
 <td><div onMouseOver="show('00')" onMouseOut="hide('00')"> ${format_player(current_players[0][0])} </div>
 <div onMouseOver="show('01')" onMouseOut="hide('01')"> ${format_player(current_players[0][1])} </div>
</td>
 <td><div onMouseOver="show('10')" onMouseOut="hide('10')"> ${format_player(current_players[1][0])} </div>
 <div onMouseOver="show('11')" onMouseOut="hide('11')">${format_player(current_players[1][1])} </div>
</td>
</tr>

<tr>
 <td>${score[0]}</td>
 <td>${score[1]}</td>
</tr>

</table>


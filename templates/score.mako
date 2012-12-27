## -*- coding: utf-8 -*-

<table class="prospetto">
<col width="380" />
<col width="380" />

<tr>
 <th>${teams[0].name}</th>
 <th>${teams[1].name}</th>
</tr>

<tr>
 <td><div onMouseOver="show('player00'); hide('player01')" onMouseOut="hide('player00')"> ${format_player(current_players[0][0])} </div>
 <div onMouseOver="show('player01'); hide('player00')" onMouseOut="hide('player01')"> ${format_player(current_players[0][1])} </div>
</td>
 <td><div onMouseOver="show('player10'); hide('player11')" onMouseOut="hide('player10')"> ${format_player(current_players[1][0])} </div>
 <div onMouseOver="show('player11'); hide('player10')" onMouseOut="hide('player11')">${format_player(current_players[1][1])} </div>
</td>
</tr>

<tr>
 <td>${score[0]}</td>
 <td>${score[1]}</td>
</tr>

</table>


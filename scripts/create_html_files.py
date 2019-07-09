import codecs
import locale
import mysql.connector


def database_connect():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="",  # enter your password to your mysql database here
        database="rift_leaderboards")
    return mydb


def mysql_leaders_html_comps(mycursor, bossid, number_of_players):
    time = "totaltime"
    if bossid == "2":
        time = "time"
    sql = "select playername, dps, time, totaltime, date, hps, class, role, a.encounterid, ptid, guildname " \
          "FROM Encounterinfo a " \
          "INNER JOIN Encounter on a.id = Encounter.encounterid " \
          "INNER JOIN Player on Encounter.playerid = Player.id " \
          "INNER JOIN Classes on Player.classid = Classes.id " \
          "INNER JOIN Roles on Encounter.roleid = Roles.id " \
          "INNER JOIN Guild on Guild.id = a.guildid " \
          "where bossid = " + bossid + " " \
          "ORDER BY " + time + ", date, Encounter.dps desc limit " + number_of_players + ""
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    return myresult


def mysql_leaders_html_fastest_kills(mycursor, bossid, number_of_players):
    mintime = " time, Min(totaltime) as mintime"
    time = "totaltime"
    if bossid == "2":
        mintime = " Min(time) as mintime, totaltime"
        time = "time"
    sql = "select Guild.guildname, sum(dps) as sum_dps, " + mintime + ", a.encounterid from Encounterinfo a " \
          "INNER JOIN Encounter on a.id = Encounter.encounterid " \
          "INNER JOIN Guild on a.guildid = Guild.id " \
          "WHERE a.bossid = " + bossid + " and a.id = ( " \
          "SELECT id from Encounterinfo b " \
          "WHERE b.bossid = " + bossid + " and b.guildid = a.guildid " \
          "ORDER BY b." + time + " limit 1) " \
          "group by Guild.guildname " \
          "ORDER BY mintime, sum_dps desc limit " + number_of_players + ""
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    return myresult


def mysql_top_dps_hps(mycursor, bossid, classid, number_of_players, role, dps_hps):
    condition = ""
    if classid:
        condition += " and Player.classid = " + classid + ""
    if role:
        condition += " and Roles.role like '%" + role + "%'"
    sql = "SELECT playername, dps AS DPS, time, totaltime, date, HPSAPS, class, role, " \
          "encounterid, ptid, aps, thps FROM ( " \
          "SELECT DISTINCT playername, dps, a.encounterid, playerid AS id, dps AS max_dps_hps ," \
          " TIME, totaltime, date, hps + aps as HPSAPS, class, role, ptid, aps, thps FROM Encounterinfo a " \
          "INNER JOIN Encounter ON a.id = Encounter.encounterid " \
          "INNER JOIN Player ON Encounter.playerid = Player.id " \
          "INNER JOIN Classes on Player.classid = Classes.id " \
          "INNER JOIN Roles on Encounter.roleid = Roles.id " \
          "WHERE bossid = " + bossid + condition + " " \
          "ORDER BY " + dps_hps + " DESC) AS top_dps_hps " \
          "GROUP BY playername " \
          "ORDER BY " + dps_hps + " DESC LIMIT " + number_of_players + ""
    # print(sql)
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    return myresult


def mysql_last_uploads(mycursor):
    sql = "SELECT date, bossname, guildname, playername, class, role, dps, hps, thps, aps, TIME, totaltime, " \
          "Encounterinfo.encounterid, ptid " \
          "FROM encounterinfo " \
          "INNER JOIN Encounter ON Encounterinfo.id = Encounter.encounterid " \
          "INNER JOIN Boss ON Encounterinfo.bossid = Boss.id " \
          "INNER JOIN Player ON Encounter.playerid = Player.id " \
          "INNER JOIN Classes on Player.classid = Classes.id " \
          "INNER JOIN Guild on Encounterinfo.guildid = Guild.id " \
          "INNER JOIN Roles on Encounter.roleid = Roles.id " \
          "ORDER BY encounterinfo.encounterid desc, Boss.id desc, dps desc " \
          "LIMIT 300"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    return myresult


def mysql_count_players_encounter(mycursor):
    sql = "SELECT COUNT(id) FROM Player"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    return myresult


def mysql_count_encounters(mycursor):
    sql = "SELECT COUNT(id) FROM Encounterinfo"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    return myresult


def mysql_count_classes(mycursor):
    sql = "SELECT class, COUNT(Player.id) as number FROM Player " \
          "INNER JOIN Classes on Player.classid = Classes.id " \
          "GROUP BY classid " \
          "ORDER BY NUMBER desc"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    return myresult


def format_number(number):
    locale.setlocale(locale.LC_NUMERIC, "german")
    number = locale.format("%.0f", number, grouping=True)
    return number


def create_url_dps(encounterid, playerid, text):
    url = "https://prancingturtle.com"
    url = '<a href="' + url + '/Encounter/Interaction?id=' + encounterid + "&p=" + playerid + \
          '&outgoing=True&type=DPS&mode=ability&filter=all" target="_blank">' + text + "</a>"
    return url


def create_url_hps(encounterid, playerid, text):
    url = "https://prancingturtle.com"
    url = '<a href="' + url + '/Encounter/Interaction?id=' + encounterid + "&p=" + playerid + \
          '&outgoing=True&type=HPS&mode=ability&filter=all" target="_blank">' + text + "</a>"
    return url


def create_url_overview(encounterid, text):
    url = "https://prancingturtle.com"
    url = '<a href="' + url + '/Encounter/PlayerDamageDone/' + encounterid + '" target="_blank">' + text + "</a>"
    return url


def exchange(mycursor, template, file, mysql_data):  # exchanges placeholders in the template file with the mysql data
    i = 0
    tbody = False
    for line in template:
        if "<tbody>" in line:
            tbody = True
        elif "</tbody>" in line:
            tbody = False
        elif "#content" in line:
            line = line.replace("#content", content(mycursor))
        elif "#guild" in line:
            guild = mysql_data[i][10]
            line = line.replace("#guild", guild)
        elif "#class" in line:
            if mysql_data[i][0] != 0:
                line = line.replace("#class", mysql_data[i][6])
            else:
                line = line.replace("#class", mysql_data[i][1])
        if tbody:
            if "#name" in line:
                if mysql_data[i][0] != 0:
                    name = str(mysql_data[i][0])
                    name = name[0:17]
                    line = line.replace("#name", name)
                else:
                    line = line.replace("#name", "")
            elif "#link" in line or "#url" in line:
                if mysql_data[i][0] != 0:
                    if "#link" in line:
                        if "#linkhps" in line:
                            name = create_url_hps(str(mysql_data[i][8]), str(mysql_data[i][9]), str(mysql_data[i][0]))
                            line = line.replace("#linkhps", name)
                        else:
                            name = create_url_dps(str(mysql_data[i][8]), str(mysql_data[i][9]), str(mysql_data[i][0]))
                            line = line.replace("#link", name)
                    else:
                        name = create_url_overview(str(mysql_data[i][4]), str(mysql_data[i][0]))
                        line = line.replace("#url", name)
                else:
                    if "linkhps" in line:
                        line = line.replace("#linkhps", "")
                    else:
                        line = line.replace("#link", "")
            elif "#dps" in line:
                if mysql_data[i][0] != 0:
                    dps = format_number(mysql_data[i][1])
                    line = line.replace("#dps", dps)
                else:
                    line = line.replace("#dps", "")
            elif "#date" in line:
                if "#datehps" in line:
                    url = create_url_hps(str(mysql_data[i][8]), str(mysql_data[i][9]), str(mysql_data[i][4]))
                    line = line.replace("#datehps", url)
                else:
                    url = create_url_dps(str(mysql_data[i][8]), str(mysql_data[i][9]), str(mysql_data[i][4]))
                    line = line.replace("#date", url)
            elif "#hps" in line:
                if mysql_data[i][0] != 0:
                    line = line.replace("#hps", format_number(mysql_data[i][5]))
                else:
                    line = line.replace("#hps", "")
            elif "#thps" in line:
                line = line.replace("#thps", format_number(mysql_data[i][11]))
            elif "#ohps" in line:
                hps = (mysql_data[i][5] - mysql_data[i][10])
                ohps = mysql_data[i][11] - hps
                line = line.replace("#ohps", format_number(ohps))
            elif "#aps" in line:
                line = line.replace("#aps", format_number(mysql_data[i][10]))
            elif "#totaltime" in line:
                if mysql_data[i][0] != 0:
                    time = str(mysql_data[i][3]).split("0:0")[1]
                    totaltime = str(mysql_data[i][2]).split("0:0")[1]
                    if time != totaltime:
                        time += " | " + totaltime
                    line = line.replace("#totaltime", time)
                else:
                    line = line.replace("#totaltime", "")
            elif "#time" in line:
                if mysql_data[i][0] != 0:
                    time = str(mysql_data[i][2]).split("0:0")[1]
                    line = line.replace("#time", time)
                else:
                    line = line.replace("#time", "")
            elif "#role" in line:
                role = mysql_data[i][7]
                if "/heal/support" in role:
                    role = role.replace("/heal/support", "/heal/s")
                elif "/support" in role:
                    role = role.replace("/support", "/supp")
                url = create_url_dps(str(mysql_data[i][8]), str(mysql_data[i][9]), role)
                # line = line.replace("#date", url)
                line = line.replace("#role", url)
            elif "#fastest_time" in line:
                time = str(mysql_data[i-1][2]).split("0:0")[1]
                line = line.replace("#fastest_time", time)
            elif "#avg" in line:
                if mysql_data[i] != 0:
                    line = line.replace("#avg", format_number(mysql_data[i]))
                else:
                    line = line.replace("#avg", "")
            if "</tr>" in line:
                i += 1
        file.write(line)


def average(data, number_of_players, dps_hps):
    dps_sum = 0
    # print(number_of_players)
    if number_of_players > 0:
        place = 1
        if dps_hps == "HPSAPS":
            place = 5
        for dps in data:
            if dps[0] != 0:
                dps_sum += (dps[place])
        dps_sum = round(dps_sum/number_of_players)
    return dps_sum


def content(mycursor):
    class_html = ""
    encounters = mysql_count_encounters(mycursor)[0][0]
    players = mysql_count_players_encounter(mycursor)[0][0]
    classes = mysql_count_classes(mycursor)
    i = 0
    for item in classes:
        if i == 0:
            class_html += str(item[1]) + " " + item[0] + "s"
        else:
            class_html += ", " + str(item[1]) + " " + item[0] + "s"
        i += 1
    html = "The Database contains " + str(players) + " Players, " + class_html + " who killed " + str(encounters) \
           + " bosses."
    return html


def leaders_html(mycursor, bossid, html_file):
    mysql_data = []
    roles = ["support", "tank", "heal"]
    template = codecs.open("template/" + html_file, 'r', "utf-8")
    file = codecs.open("public/" + html_file, 'w', "utf-8")
    number_of_players = 10
    for boss_id in bossid:
        data = mysql_leaders_html_fastest_kills(mycursor, str(boss_id), str(number_of_players))
        mysql_data += data + [average(data, number_of_players, "DPS")]
    for boss_id in bossid:
        data = mysql_leaders_html_comps(mycursor, str(boss_id), str(number_of_players))
        mysql_data += data + [average(data, number_of_players, "DPS")]
    number_of_players = 15
    for boss_id in bossid:
        data = mysql_top_dps_hps(mycursor, str(boss_id), "", str(number_of_players), "", "DPS")
        mysql_data += data + [average(data, number_of_players, "DPS")]
    number_of_players = 10
    for role in roles:
        for boss_id in bossid:
            data = mysql_top_dps_hps(mycursor, str(boss_id), "", str(number_of_players), role, "DPS")
            mysql_data += data + [average(data, number_of_players, "DPS")]
    exchange(mycursor, template, file, mysql_data)
    file.close()
    template.close()
    print("public/" + html_file + " created")


def dps_html(mycursor, bossid, classid, html_file):
    mysql_data = []
    template = codecs.open("template/" + html_file, 'r', "utf-8")
    file = codecs.open("public/" + html_file, 'w', "utf-8")
    number_of_players = 10
    role = ""
    for boss_id in bossid:
        for class_id in classid:
            data = mysql_top_dps_hps(mycursor, str(boss_id), str(class_id), str(number_of_players), role, "DPS")
            mysql_data += data + [average(data, number_of_players, "DPS")]
    exchange(mycursor, template, file, mysql_data)
    file.close()
    template.close()
    print("public/" + html_file + " created")


def tank_sup_dps_hps_html(mycursor, bossid, classid, role, sort_order, html_file):
    mysql_data = []
    template = codecs.open("template/" + html_file, 'r', "utf-8")
    file = codecs.open("public/" + html_file, 'w', "utf-8")
    number_of_players = 10
    for boss_id in bossid:
        for class_id in classid:
            data = mysql_top_dps_hps(mycursor, str(boss_id), str(class_id), str(number_of_players), role, sort_order)
            # print(len(data))
            if len(data) < number_of_players:
                players = len(data)
                for i in range(number_of_players - players):
                    data += [(0, class_classid(class_id))]
                mysql_data += data + [average(data, players, sort_order)]
            else:
                mysql_data += data + [average(data, number_of_players, sort_order)]
    exchange(mycursor, template, file, mysql_data)
    file.close()
    template.close()
    print("public/" + html_file + " created")


def hps_html(mycursor, bossid, classid, html_file):
    mysql_data = []
    template = codecs.open("template/" + html_file, 'r', "utf-8")
    file = codecs.open("public/" + html_file, 'w', "utf-8")
    number_of_players = 15
    for boss_id in bossid:
        if boss_id != 2:
            data = mysql_top_dps_hps(mycursor, str(boss_id), "", str(number_of_players), "", "HPSAPS")
            mysql_data += data + [average(data, number_of_players, "HPSAPS")]
    number_of_players = 10
    for class_id in classid:
        for boss_id in bossid:
            if boss_id != 2:
                data = mysql_top_dps_hps(mycursor, str(boss_id), str(class_id), str(number_of_players), "", "HPSAPS")
                mysql_data += data + [average(data, number_of_players, "HPSAPS")]
    exchange(mycursor, template, file, mysql_data)
    file.close()
    template.close()
    print("public/" + html_file + " created")


def most_played_specs_html(mycursor, html_file):
    template = codecs.open("template/" + html_file, 'r', "utf-8")
    file = codecs.open("public/" + html_file, 'w', "utf-8")
    for line in template:
        if "#content" in line:
            line = line.replace("#content", content(mycursor))
        file.write(line)
    file.close()
    template.close()
    print("public/" + html_file + " created")


def las_uploads_html(mycursor, html_file):
    html = []
    table = False
    template = codecs.open("template/" + html_file, 'r', "utf-8")
    file = codecs.open("public/" + html_file, 'w', "utf-8")
    mysql_data = mysql_last_uploads(mycursor)
    for line in template:
        if "<!-- row template here -->" in line:
            table = True
            html += ['            <!-- row template here -->\n']
            for item in mysql_data:
                html += ['            <tr>\n']
                i = 0
                for data in item:
                    i += 1
                    if type(data) == int:
                        data = format_number(data)
                    if i == 1:
                        encounterid = item[12]
                        playerid = item[13]
                        html += ['                <td scope="row">'
                                 + create_url_dps(str(encounterid), str(playerid), str(data)) + '</td>\n']
                    elif i == 11 or i == 12:
                            html += ['                <td scope="col">' + str(data).split("0:")[1] + '</td>\n']
                    else:
                        html += ['                <td scope="col">' + str(data) + '</td>\n']
                    if i == 12:
                        break
                html += ['            </tr>\n']
        if "<!-- end row template -->" in line:
            table = False
        else:
            if not table:
                html += [line]
    for line in html:
        if "#content" in line:
            line = line.replace("#content", content(mycursor))
        file.write(line)
    file.close()
    template.close()
    print("public/" + html_file + " created")


def class_classid(class_id):
    classname = ""
    if class_id == 1:
        classname = "Cleric"
    elif class_id == 2:
        classname = "Mage"
    elif class_id == 3:
        classname = "Primalist"
    elif class_id == 4:
        classname = "Rogue"
    elif class_id == 5:
        classname = "Warrior"
    return classname


def main():
    bossid = [1, 2, 3, 4]  # 1 Azranel, 2 Vindicator MK1, 3 Commander Isiel, 4 Titan X
    mydb = database_connect()
    mycursor = mydb.cursor()
    database_connect()
    leaders_html(mycursor, bossid, "index.html")
    classid = [4, 3, 5, 2, 1]  # 1 Cleric, 2 Mage, 3 Primalist, 4 Rogue, 5 Warrior
    dps_html(mycursor, bossid, classid, "dps.html")
    classid = [2, 5, 3, 4, 1]
    hps_html(mycursor, bossid, classid, 'hps.html')
    classid = [3, 2, 1, 4, 5]
    tank_sup_dps_hps_html(mycursor, bossid, classid, "support", "DPS", "supdps.html")
    classid = [4, 1, 2, 3, 5]
    tank_sup_dps_hps_html(mycursor, bossid, classid, "support", "HPSAPS", "suphps.html")
    classid = [1, 4, 3, 2, 5]
    tank_sup_dps_hps_html(mycursor, bossid, classid, "tank", "DPS", "tdps.html")
    classid = [2, 4, 1, 3, 5]
    tank_sup_dps_hps_html(mycursor, bossid, classid, "tank", "HPSAPS", "thps.html")
    most_played_specs_html(mycursor, "mostplayed.html")
    las_uploads_html(mycursor, "latestuploads.html")


if __name__ == "__main__":
    main()
#Requires AutoHotkey v2.0

; --- Настройка клавиш ---
global FastOffOnKey := "F3" ; Замените на любую клавишу которую хотите использовать для быстрого включения/выключения
global MoveKey := "F1" ; Замените на любую клавишу которую хотите использовать для показа/скрытия верхней панели и кнопок окна
global MessegesKey := "F7" ; Замените на любую клавишу которую хотите использовать для отправки шаблонных сообщений
global HideToggleKey := "F6" ; Замените на любую клавишу которую хотите использовать для показа/скрытия панели

; --- Переменные ---
global LastRole := ""
global Role := ""
global HeadCode := ""
global Tixt := ""
global StationType := ""
global Station := ""
global Moving := true
global isGuiVisible := false
global Working := false
global MainFn := 0

; --- Масивы ---
RoleMessages := Map(
	"GD", ["Someone need GD?", "Nearest station?", "[DS ST] Safe shift!"],
	"DS", ["[HC] Safe trip!", "[HC] Safe trip & GD!"],
	"QD", ["Free GD?", "Nearest station - ST", "[DS ST] Safe shift!"],
	"SG", ["Zone # on manual control!", "Zone # on automatic control!", "[DS ST] please dispatch HC!"],
	"OFF", ["Выберите роль!"]
)

Stationlist := Map(
	true, ["Angel Pass", "Airport Central", "Airport Parkway", "Airport West", "Benton Bridge", "Barton", "Beechley", "Benton", "Bodin", "Beaulieu Park", "Berrily", "City Hospital", "Coxly Newtown", "Connolly", "Coxly", "Cambridge Street Parkway", "East Berrily", "Eden Quay", "Esterfield", "Edgemead", "Elsemere Junction", "Farleigh", "Faymere", "Faraday Road", "Financial Quarter", "Four Ways", "Greenslade", "High Street", "Leighton Stepford Road", "Leighton City", "Llyn-by-the-Sea", "Millcastle", "Morganstown", "Newry Harbour", "Newry", "Northshore", "Port Benton", "Rayleigh Bay", "Terminal 1", "Terminal 2", "Terminal 3", "Stepford Central", "Stepford Victoria", "St Helens Bridge", "Stepford East", "Stepford United Football Club", "West Benton", "Willowfield", "Woodhead Lane", "Whitefield Lido", "Water Newton", "Westercoast", "Westwyvern"],
	false, ["Angel Pass", "AC", "AP", "AW", "BB", "Barton", "Beechley", "Benton", "Bodin", "BP", "Berrily", "CH", "CN", "Connolly", "Coxly", "CSP", "EB", "EQ", "Esterfield", "Edgemead", "EJ", "Farleigh", "Faymere", "FR", "FQ", "FW", "Greenslade", "HS", "LSR", "LC", "LBTS", "Millcastle", "Morganstown", "NH", "Newry", "Northshore", "PB", "RB", "T1", "T2", "T3", "SC", "SV", "SHB", "SE", "UFC", "WB", "WF", "WHL", "WFL", "WN", "WC", "WW"]
)

; --- GUI ---
myGui := Gui("+AlwaysOnTop -SysMenu -Caption", "SCR")
myGui.BackColor := 0x000000
myGui.Icon := "C:\Users\Wlad\Downloads\Ahk\Icons\SCR.ico"
myGui.SetFont("s16 w700", "Arial Black")
myGui.opt("+SysMenu +Caption")

; --- Роль ---
global Text1 := myGui.Add("Text", "cffffff", "Роль")
global RoleList := myGui.Add("dropdownList", "w80 r5 Choose1", ["OFF", "GD", "DS", "QD", "SG"])
RoleList.OnEvent("Change", RoleUpdate)

; --- Текст ---
myGui.Add("Text", "cFFFFFF", "Текст")
global TextList := myGui.Add("dropdownList", "w360 r3")
TextList.OnEvent("Change", TextUpdate)

; --- Станция ---
myGui.Add("Text", "cFFFFFF", "Станция")
global StationBox := myGui.Add("ComboBox", "Simple w380 r2")
StationBox.Add(Stationlist[false])
StationBox.Choose(1)
StationBox.OnEvent("Change", StationUpdate)

global StationTypeBox := MyGui.Add("CheckBox", "w360 cFFFFFF", "Полное название станций")
StationTypeBox.OnEvent("Click", StationTypeUpdate)


; --- ГоловнойКод ---
myGui.Add("Text", "cFFFFFF", "HeadCode")
global Code := myGui.Add("Edit", "Limit4 Uppercase w80 r1")
Code.OnEvent("Change", CodeUpdate)



; --- Функции ---

RoleUpdate(*) {
	global Role, RoleList, TextList, LastRole, RoleMessages
	Role := RoleList.Text
	TextList.Delete()

	if Role = "OFF" {
		StopTesting()
	} else {
		LastRole := Role
		StartTesting()
	}

	if RoleMessages.Has(Role) {
		TextList.Add(RoleMessages[Role])
		TextList.Choose(1)
	}
}

CodeUpdate(ctrl, info) {
	global HeadCode
	HeadCode := ctrl.Text
}

TextUpdate(ctrl, info) {
	global Tixt
	Tixt := ctrl.Text
}

StationTypeUpdate(ctrl, info) {
	global StationBox, StationList, StationType

	if StationType {
		StationType := false
	} else {
		StationType := true
	}

	StationBox.Delete
	if Stationlist.Has(StationType) {
		StationBox.Add(Stationlist[StationType])
		StationBox.Choose(1)
	}
}
StationUpdate(ctrl, info) {
	global Station
	Station := ctrl.Text
}

Print(ctrl) {
	SendInput("{/}")
	Sleep 100
	SendInput(ctrl)
	Sleep 100
	SendInput("{Enter}")
}

StartTesting() {
	global Working, MainFn
	if ProcessExist() { 
		Working := true
		MainFn := Main
		SetTimer(MainFn, 1)
	}
}

StopTesting() {
	global Working, MainFn
	Working := false
	if (MainFn) {
		SetTimer(MainFn, 0)
		MainFn := 0
	}
}

Main() {
	global Role
	
	try {
		if (Role = "GD") {
			if (PixelGetColor(143, 570, "RGB") = 0xF7A502) {
				Send("{E}")
			}

			if (PixelGetColor(1720, 595, "RGB") = 0xE84AB6) {
				Send("{Q}")
			}

			if (PixelGetColor(120, 600, "RGB") = 0x0056DF) {
				Send("{Y}")
			}

			if (PixelGetColor(120, 400, "RGB") = 0x00DCDC) {
				Send("{Q}")
			}

			if (PixelGetColor(1795, 595, "RGB") = 0xE84AB6) {
				Send("{R}")
			}

			if (PixelGetColor(102, 725, "RGB") = 0xECF4FD) {
				Send("{E}")
			}

			if (PixelGetColor(120, 500, "RGB") = 0xEA0000) {
				Send("{T}")
			}
		}

		if (Role = "DS") {
			if (PixelGetColor(1710, 605, "RGB") = 0xE84AB6) {
				Send("{Q}")
			}

			if (PixelGetColor(1785, 605, "RGB") = 0xE84AB6) {
				Send("{T}")
			}

			if (PixelGetColor(1860, 605, "RGB") = 0xE84AB6) {
				Send("{R}")
			}
		}

		if (Role = "QD") {
			if (PixelGetColor(1765, 850, "RGB") = 0xFFAA00) {
				Send("{Q}")
			}

			if (PixelGetColor(1720, 910, "RGB") = 0xFF3D3D) {
				Send("{Q}")
			}

			if (PixelGetColor(1400, 690, "RGB") = 0xE84AB6) {
				Send("{T}")
			}

			if (PixelGetColor(350, 760, "RGB") = 0xE84AB6) {
				Send("{T}")
			}

			if (PixelGetColor(1400, 690, "RGB") = 0x2D8EF9) {
				Send("{T}")
			}
		}
	}
}

; --- Сообщение ---
Messeges(*) {
	global Role, HeadCode, Tixt, Station
	

	if (Role = "GD") {
		if (Tixt = "Someone need GD?") {
			Print("Someone need GD?")
		}
		else if (Tixt = "Nearest station?") {
			Print("Nearest station?")
		}
		else if (Tixt = "[DS ST] Safe shift!") {
			Print("[DS " Station "] Safe shift!")
		}
	}
	else if (Role = "DS") {
		if (Tixt = "[HC] Safe trip!") {
			Print("[" HeadCode "] Safe trip!")
		}
		else if (Tixt = "[HC] Safe trip & GD!") {
			Print("[" HeadCode "] Safe trip & GD!")
		}
	}
	else if (Role = "QD") {
		if (Tixt = "Free GD?") {
			Print("Free GD?")
		}
		else if (Tixt = "Nearest station - ST") {
			Print("Nearest station - " Station)
		}
		else if (Tixt = "[DS ST] Safe shift!") {
			Print("[DS " Station "] Safe shift!")
		}
	}
	else if (Role = "SG") {
		if (Tixt = "Zone # on manual control!") {
			Print("Zone " HeadCode " on manual control!")
		}
		else if (Tixt = "Zone # on automatic control!") {
			Print("Zone " HeadCode " on automatic control!")
		}
		else if (Tixt = "[DS ST] please dispatch HC!") {
			Print("[DS " Station "] please dispatch " HeadCode "!")
		}
	}
}

; --- Скрыть/Показать ---
HideToggle(*) {
	global isGuiVisible, myGui
	isGuiVisible := !isGuiVisible
	if isGuiVisible
		myGui.Show()
	else
		myGui.Hide()
}

; --- Быстрое ВЫКЛ/ВКЛ ---
FastOffOn(*) {
	global Working, RoleList, LastRole
	if Working {
		RoleList.Choose("OFF")
		StopTesting()
	} else {
		RoleList.Choose(LastRole)
		StartTesting()
	}
}

; --- Перетаскивание ---
Move(*) {
	global Moving, myGui
	if Moving {
		myGui.opt("-SysMenu -Caption")
		Moving := false
	} else {
		myGui.opt("+SysMenu +Caption")
		Moving := true
	}
}

Hotkey(FastOffOnKey, FastOffOn)
Hotkey(MoveKey, Move)
Hotkey(MessegesKey, Messeges)
Hotkey(HideToggleKey, HideToggle)
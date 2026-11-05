// Greek name days (γιορτές) for the "Name Day" card.
//
// Covers the widely celebrated name days only. Dates follow the Greek Orthodox calendar.
// Each entry: [Greek name, everyday English spelling].

// Fixed-date name days, keyed "MM-DD".
const FIXED_NAMEDAYS = {
    "01-01": [["Βασίλης", "Vasilis"], ["Βασιλική", "Vasiliki"]],
    "01-06": [["Φώτης", "Fotis"], ["Φωτεινή", "Fotini"], ["Θεοφάνης", "Theofanis"], ["Θεοφανία", "Theofania"]],
    "01-07": [["Γιάννης", "Giannis"], ["Ιωάννα", "Ioanna"]],
    "01-17": [["Αντώνης", "Antonis"], ["Αντωνία", "Antonia"]],
    "01-18": [["Θανάσης", "Thanasis"], ["Αθανασία", "Athanasia"], ["Κύριλλος", "Kyrillos"]],
    "01-20": [["Ευθύμιος", "Efthymios"]],
    "01-25": [["Γρηγόρης", "Grigoris"]],
    "02-01": [["Τρύφων", "Tryfon"]],
    "02-10": [["Χαράλαμπος", "Charalambos (Babis)"]],
    "02-11": [["Βλάσης", "Vlasis"]],
    "03-25": [["Βαγγέλης", "Vangelis"], ["Ευαγγελία", "Evangelia"]],
    "05-05": [["Ειρήνη", "Irini"]],
    "05-21": [["Κώστας", "Kostas"], ["Κωνσταντίνα", "Konstantina"], ["Ελένη", "Eleni"]],
    "06-11": [["Βαρνάβας", "Varnavas"], ["Βαρθολομαίος", "Vartholomaios"]],
    "06-29": [["Πέτρος", "Petros"], ["Παύλος", "Pavlos"]],
    "06-30": [["Απόστολος", "Apostolos"]],
    "07-01": [["Κοσμάς", "Kosmas"], ["Δαμιανός", "Damianos"]],
    "07-07": [["Κυριακή", "Kyriaki"]],
    "07-11": [["Ευφημία", "Efimia"]],
    "07-17": [["Μαρίνα", "Marina"]],
    "07-20": [["Ηλίας", "Ilias"]],
    "07-22": [["Μαγδαληνή", "Magdalini"]],
    "07-24": [["Χριστίνα", "Christina"]],
    "07-26": [["Παρασκευή", "Paraskevi (Evi)"]],
    "07-27": [["Παντελής", "Pantelis"]],
    "08-06": [["Σωτήρης", "Sotiris"], ["Σωτηρία", "Sotiria"]],
    "08-15": [["Μαρία", "Maria"], ["Παναγιώτης", "Panagiotis"], ["Παναγιώτα", "Panagiota"], ["Δέσποινα", "Despina"], ["Μάριος", "Marios"]],
    "08-30": [["Αλέξανδρος", "Alexandros"]],
    "09-14": [["Σταύρος", "Stavros"], ["Σταυρούλα", "Stavroula"]],
    "09-17": [["Σοφία", "Sofia"], ["Ελπίδα", "Elpida"], ["Αγάπη", "Agapi"], ["Πίστη", "Pisti"]],
    "09-20": [["Ευστάθιος", "Efstathios (Stathis)"]],
    "10-03": [["Διονύσης", "Dionysis"]],
    "10-06": [["Θωμάς", "Thomas"]],
    "10-18": [["Λουκάς", "Loukas"]],
    "10-26": [["Δημήτρης", "Dimitris"], ["Δήμητρα", "Dimitra"]],
    "11-05": [["Γαλακτίων", "Galaktion"], ["Επιστήμη", "Epistimi"]],
    "11-08": [["Μιχάλης", "Michalis"], ["Γαβριήλ", "Gavriil"], ["Άγγελος", "Angelos"], ["Αγγελική", "Angeliki"]],
    "11-11": [["Μηνάς", "Minas"]],
    "11-14": [["Φίλιππος", "Filippos"]],
    "11-16": [["Ματθαίος", "Matthaios"]],
    "11-25": [["Κατερίνα", "Katerina"]],
    "11-26": [["Στέλιος", "Stelios"], ["Στυλιανή", "Styliani"]],
    "11-30": [["Ανδρέας", "Andreas"]],
    "12-04": [["Βαρβάρα", "Varvara"]],
    "12-05": [["Σάββας", "Savvas"]],
    "12-06": [["Νίκος", "Nikos"], ["Νικολέτα", "Nikoleta"]],
    "12-09": [["Άννα", "Anna"]],
    "12-12": [["Σπύρος", "Spyros"]],
    "12-15": [["Λευτέρης", "Lefteris"], ["Ελευθερία", "Eleftheria"]],
    "12-22": [["Αναστασία", "Anastasia"]],
    "12-25": [["Χρήστος", "Christos"]],
    "12-27": [["Στέφανος", "Stefanos"], ["Στεφανία", "Stefania"]],
};

const GEORGE = [["Γιώργος", "Giorgos"], ["Γεωργία", "Georgia"]];
const MARK = [["Μάρκος", "Markos"]];

// Orthodox Easter Sunday (Gregorian date) for a given year, valid 1900-2099.
function orthodoxEaster(year) {
    const a = year % 4, b = year % 7, c = year % 19;
    const d = (19 * c + 15) % 30;
    const e = (2 * a + 4 * b - d + 34) % 7;
    const month = Math.floor((d + e + 114) / 31);   // Julian calendar month
    const day = ((d + e + 114) % 31) + 1;
    const julian = new Date(Date.UTC(year, month - 1, day));
    julian.setUTCDate(julian.getUTCDate() + 13);    // Julian -> Gregorian
    return julian;
}

function addDays(date, days) {
    const d = new Date(date);
    d.setUTCDate(d.getUTCDate() + days);
    return d;
}

function sameDay(a, b) {
    return a.getUTCFullYear() === b.getUTCFullYear() && a.getUTCMonth() === b.getUTCMonth() && a.getUTCDate() === b.getUTCDate();
}

// Returns the names celebrating on the given (year, month 1-12, day).
function getNamedays(year, month, day) {
    const date = new Date(Date.UTC(year, month - 1, day));
    const key = `${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const names = [...(FIXED_NAMEDAYS[key] || [])];

    const easter = orthodoxEaster(year);
    const georgeFixed = new Date(Date.UTC(year, 3, 23));
    const markFixed = new Date(Date.UTC(year, 3, 25));

    // Easter Sunday: Lambros/Lambrini and Anastasios
    if (sameDay(date, easter)) {
        names.push(["Λάμπρος", "Lambros"], ["Λαμπρινή", "Lambrini"], ["Αναστάσιος", "Anastasios (Tasos)"]);
    }

    // St George (23 April) moves to Easter Monday if it falls on or before Easter Sunday.
    const georgeDay = georgeFixed <= easter ? addDays(easter, 1) : georgeFixed;
    if (sameDay(date, georgeDay)) names.push(...GEORGE);

    // St Mark (25 April) moves to Easter Tuesday if it falls on or before Easter Monday.
    const markDay = markFixed <= addDays(easter, 1) ? addDays(easter, 2) : markFixed;
    if (sameDay(date, markDay)) names.push(...MARK);

    return names;
}

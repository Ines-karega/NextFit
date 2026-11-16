// Fills the "district" dropdown with the districts of the chosen province.
var LOCATIONS = JSON.parse(document.getElementById("locations").textContent);

function fillDistricts(provinceSelect, districtSelect) {
  var chosen = districtSelect.getAttribute("data-selected") || districtSelect.value;
  var province = provinceSelect.value;
  districtSelect.innerHTML = "";

  var first = document.createElement("option");
  first.value = "";
  first.textContent = districtSelect.getAttribute("data-empty") || "Choose district";
  districtSelect.appendChild(first);

  var list = LOCATIONS[province] || [];
  for (var i = 0; i < list.length; i++) {
    var option = document.createElement("option");
    option.value = list[i];
    option.textContent = list[i];
    if (list[i] === chosen) { option.selected = true; }
    districtSelect.appendChild(option);
  }
  districtSelect.removeAttribute("data-selected");
}

var provinceBoxes = document.querySelectorAll("select.province");
for (var i = 0; i < provinceBoxes.length; i++) {
  (function (provinceSelect) {
    var districtSelect = provinceSelect.form.querySelector("select.district");
    fillDistricts(provinceSelect, districtSelect);
    provinceSelect.addEventListener("change", function () {
      fillDistricts(provinceSelect, districtSelect);
    });
  })(provinceBoxes[i]);
}

// Adds a "Show password" tick box under every password box, so people can
// check what they typed. Ticking it shows the letters; unticking hides them again.
var passwordBoxes = document.querySelectorAll('input[type="password"]');
for (var j = 0; j < passwordBoxes.length; j++) {
  (function (passwordBox) {
    var tick = document.createElement("input");
    tick.type = "checkbox";
    var label = document.createElement("label");
    label.className = "check show-password";
    label.appendChild(tick);
    label.appendChild(document.createTextNode(" Show password"));
    passwordBox.insertAdjacentElement("afterend", label);
    tick.addEventListener("change", function () {
      passwordBox.type = tick.checked ? "text" : "password";
    });
  })(passwordBoxes[j]);
}

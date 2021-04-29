
const RECAPTCHA_BUTTON = "recaptcha-button"
const RECAPTCHA_BOX = "recaptcha-box"
const RECAPTCHA_AREA = "recaptcha-area"

const RECAPTCHA_BOX_CLASS_DISABLED = "recaptcha-disabled"
const RECAPTCHA_BOX_CLASS_ENABLED = "recaptcha-enabled"

var recaptchaAreas = $(`*[id*=${RECAPTCHA_AREA}]`)
var index = 0

for (; index < recaptchaAreas.length; index++) {
    var area = recaptchaAreas[index];

    area.querySelector(`#${RECAPTCHA_BUTTON}`).onclick = (event) => {
        var button = event.target
        var local_index = button.id.replace(`${RECAPTCHA_BUTTON}-`,"")
        var box = document.getElementById(`${RECAPTCHA_BOX}-${local_index}`);
        
        button.type = "submit"
        button.disabled = "true"
        setTimeout(function(){button.disabled = false;},1000);

        box.classList.remove(RECAPTCHA_BOX_CLASS_DISABLED)    
        box.classList.add(RECAPTCHA_BOX_CLASS_ENABLED)
    } 

    area.querySelector(`#${RECAPTCHA_BOX}`).classList.add(RECAPTCHA_BOX_CLASS_DISABLED)    
    area.querySelector(`#${RECAPTCHA_BOX}`).id = `${RECAPTCHA_BOX}-${index}`
    area.querySelector(`#${RECAPTCHA_BUTTON}`).id = `${RECAPTCHA_BUTTON}-${index}`
}

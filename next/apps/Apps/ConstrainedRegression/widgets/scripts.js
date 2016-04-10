/**
 * Get a random integer between `min` and `max`.
 *
 * @param {number} min - min number
 * @param {number} max - max number
 * @return {int} a random integer
 */
function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min);
}

document.getElementById("alternative").innerHTML = "$" + getRandomInt(0, 1000) + " today"

delayInMonths = document.getElementById("delay").innerHTML;
delayPrettyPrint = moment().add(delayInMonths, 'months').fromNow();
document.getElementById("alternative2").innerHTML = "$1000 " + delayPrettyPrint;

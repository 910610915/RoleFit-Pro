
const si = require('systeminformation');

async function test() {
    try {
        console.log("--- Block Devices ---");
        const blocks = await si.blockDevices();
        console.log(JSON.stringify(blocks, null, 2));

        console.log("\n--- Disks IO ---");
        const io = await si.disksIO();
        console.log(JSON.stringify(io, null, 2));

        console.log("\n--- FS Stats ---");
        const fs = await si.fsStats();
        console.log(JSON.stringify(fs, null, 2));
    } catch (e) {
        console.error(e);
    }
}

test();

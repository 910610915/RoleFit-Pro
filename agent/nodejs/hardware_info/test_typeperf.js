
const { exec } = require('child_process');

const cmd = 'typeperf "\\PhysicalDisk(*)\\Current Disk Queue Length" "\\PhysicalDisk(*)\\Avg. Disk sec/Transfer" "\\PhysicalDisk(*)\\Disk Read Bytes/sec" "\\PhysicalDisk(*)\\Disk Write Bytes/sec" -sc 1';

console.log("Running:", cmd);

exec(cmd, (error, stdout, stderr) => {
    if (error) {
        console.error(`exec error: ${error}`);
        return;
    }
    console.log(`stdout: ${stdout}`);
    if (stderr) console.error(`stderr: ${stderr}`);
});

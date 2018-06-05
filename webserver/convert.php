<!DOCTYPE HTML>
<html>

<head>
  <title>FRM3 D-Flash to EEPROM converter</title>
  <meta name="description" content="A tool to fix your FRM" />
  <meta name="keywords" content="bmw mini frm frm3 footwell repair d-flash eeprom MC9S12XEQ384 MC9S12XEQ512" />
  <meta http-equiv="content-type" content="text/html; charset=windows-1252" />
</head>

<body>
  <div id="main">
    <?php
    require("settings.php");

    if(!isset($_POST["submit"]) || $_POST["submit"] != "Upload") {
        echo "<p>Something went wrong, please go back to the <a href=\".\">main page</a></p>";
    }
    else {
        if($_POST["storeagreed"] != "yes") {
            echo "<p>You can only use this tool if you agree to store the file on our servers.</p>";
        }
        else {
            $size = $_FILES["dflashimage"]["size"];
            if($size != $required_size) {
                echo "<p>Uploaded file is not the correct size! Please double check that you saved the complete D-Flash image</p>";
            }
            else {
                /* The checks we can do in PHP seems to be passed. Save the file under its sha1sum and then execute the python script */
                $sha1 = sha1_file($_FILES["dflashimage"]["tmp_name"]);
                $target = $target_path . "/" . $sha1 . ".bin";
                $logfile = $logfile_path . "/" . $sha1 . ".txt";
                if (!move_uploaded_file($_FILES["dflashimage"]["tmp_name"], $target)) {
                    echo "<p>Error moving file to target. Please contact the administrator</p>";
                }
                else {
                    // Also use the sha1 of the source for the eeprom file, since we can't know that beforehand.
                    $eepromfile = $result_path . "/" . $sha1 . ".bin";
                
                    $descriptorspec = array(
                       0 => array("pipe", "r"),  // stdin
                       1 => array("pipe", "w"),  // stdout
                       2 => array("pipe", "w"),  // stderr
                    );
                    $process = proc_open('../dflash_to_eee.py ' . $target . ' ' . $eepromfile, $descriptorspec, $pipes);
                    
                    $stdout = stream_get_contents($pipes[1]);
                    fclose($pipes[1]);

                    $stderr = stream_get_contents($pipes[2]);
                    fclose($pipes[2]);

                    $logfp = fopen($logfile, "w");
                    fwrite($logfp, $stdout);
                    fwrite($logfp, $stderr);
                    fclose($logfp);

                    echo "<h1>Conversion complete.</h1>";
                    
                    echo "<h3>Logfile: </h3>";
                    echo "<pre>";
                    echo($stdout);
                    echo($stderr);
                    echo "</pre>";

                    echo "<p>Before downloading, ensure that the VIN is correct.</p>";

                    echo "<h2><a href=\"download.php?sha1=" . $sha1 . "\">Download EEPROM image</a></h2>";

                    echo "<h2><strong>Note:</strong> Ensure you write to EEE partition and not back to D-Flash!</h2>";
                    echo "<h2><strong>Note:</strong> Always verify after writing the image to the device!</h2>";
                }
            }
        }
    }
?>
    <p><a href="https://gitlab.com/tomvleeuwen/dflash_to_eeprom">Source code</a></p>
    <p><a href="https://gitlab.com/tomvleeuwen/dflash_to_eeprom/tags/1.1">Offline version</a></p>
  </div>
</body>

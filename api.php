<?php
/**
 * API Framework for controlling parsing
 * 
 * @category API
 * @package  PageLevel_Package
 * @author   g183515 <shadow7en@ya.ru>
 * @license  http://opensource.org/licenses/gpl-license.php GNU Public License
 * @link     https://github.com/Guest0131/hh_parser
 */

//Global Vars
$GLOBALS['iniFileName'] = 'settings.ini';
$GLOBALS['parserArr']  = [
    'headHunter' => 'parser.py'
];

/**
 * API for HeadHunter

 * @category API
 * @package  ClassLevel_Package
 * @author   g183515 <shadow7en@ya.ru>
 * @license  http://opensource.org/licenses/gpl-license.php GNU Public License
 * @link     https://github.com/Guest0131/hh_parser
 */
class ApiHeadHunterParser
{

    //Config vars
    public $iniData;
    public $params;
    public $methodsArr;

    /**
     * Construction method.
     * 
     * Checking params in GET and execute appropriate function.
     */
    public function __construct()
    {

        //Init vars
        $this->iniData = parse_ini_file($GLOBALS['iniFileName']);
        $this->params  = $_GET;
        $this->methodsArr = [
            'status', 'execute', 'checkConnect'
        ];

        //Convert url
        if (isset($this->params['url'])) {
            $this->params['url'] = base64_decode($this->params['url']);
        }

        //Check auth
        $this->_checkAuth();

        //Get method and switchin here
        $methodName = $this->_getMethodName();
        switch ($methodName) {
        case 'status' :
            $this->parseStatus();
            break;
        case 'execute' :
            if (isset($this->params['url']) and isset($this->params['mode'])) {
                $this->executeParse($this->params['url'], $this->params['mode']);
                break;
            } else {
                $this->_printError('params');
            }
        default :
            echo json_encode(array('connect' => 'succeed'));
        }
        
    }

    
    /**
     * Execute parsing task.
     *
     * @param string $url    Url on hh.ru
     * @param string $method [current, all]
     * 
     * @return void
     */
    public function executeParse(string $url, string $method)
    {
        //Check correct method
        if (!in_array($method, array('current', 'all'))) {
            $this->_printError('params');
        }

        //Templates exec commands
        $currentCmd = 'python '.$GLOBALS['parserArr']['headHunter']." -c $url";
        $allCmd     = 'python '.$GLOBALS['parserArr']['headHunter']." -a $url";

        switch($method) {
        case 'current' :
            exec($currentCmd, $out, $ret);
            break;
        case 'all' :
            exec($allCmd, $out, $ret);
            break;
        }
    }

    /**
     * Return count parse task(s) on server
     *
     * @return void
     */
    public function parseStatus()
    {
        if (isset($this->iniData['status'])) {
            echo json_encode($this->iniData['status']);
            return;
        } else {
            $this->_printError('ini');
        }
    }

    /**
     * Function checking correcting token
     *
     * @return void
     */
    private function _checkAuth()
    {
        //Check api_token in .ini file
        if (!array_key_exists('api_token', $this->iniData)) {
            $this->_printError('ini');
        }

        //Check user api_token
        if (isset($this->params['token']) and $this->iniData['api_token'] == $this->params['token']) {
            return;
        } else {
            $this->_printError('auth');
        }
    }

    /**
     * Check correct method name and get method name, if here coorect set
     *
     * @return void or string
     */
    private function _getMethodName()
    {

        if (in_array($this->params['method'], $this->methodsArr)) {
            return $this->params['method'];
        } else {
            $this->_printError('method');
        }
    }

    /**
     * Printing any error
     *
     * @param string $message Type error.
     * 
     * @return void
     */
    private function _printError(string $message)
    {
        switch($message) {
        case 'ini' :
            echo json_encode(array('error' => 'Not found field in .ini file!'));
            exit();
        case 'params' :
            echo json_encode(array('error' => 'No correct set params!'));
            exit();
        case 'auth' :
            echo json_encode(array('error' => 'Bad token!'));
            exit();
        case 'method' :
            echo json_encode(array('error' => 'Uncorrect method name!'));
            exit();
        default:
            echo json_encode(array('error' => 'Error!'));
            exit();
        }
    }


};

$x = new ApiHeadHunterParser();
?>
// ============================== SUMMARY =====================================
//
// Program : google_groups_auth.go
// Version : 1.0.go 
// Date    : 05.07.2018
// Author  : Marcin Kowalczuk - marcin.kowalczuk(at)rtbhouse.com
// Licence : GPL - summary below, full text at http://www.fsf.org/licenses/gpl.txt
//
//------------------------------------------------------------------------------------
package main

import (
	"fmt"
	"os"
	"bufio"
	"encoding/json"
	"encoding/base64"
	"strings"
	"log"
	"golang.org/x/net/context"
	"google.golang.org/api/admin/directory/v1"
	"io/ioutil"
	"golang.org/x/oauth2/google"
	"errors"
	"github.com/patrickmn/go-cache"
	"time"
)
//##############################################################################

type Configuration struct {
	GoogleScope	string
	ServiceAccountFile	string
	SubjectAccount	string
	LogFile	string
	Base64Encrypt	bool
}

//##############################################################################
func hasMember(user, group string) bool {

	var key string
	key = user + "#" + group
	log.Printf("CACHE - ask for AUTH key: %s", key)
	val, found := c.Get(key)
	if found{
		log.Printf("CACHE - Found key: %s in cache", key)
		//debug*** //fmt.Printf("z cache ------ %B\n",val)
		return val.(bool)
	}else{
		// ask google
		log.Printf("CACHE - Do not found key: %s in cache\n", key)
		log.Printf("AUTH  - connect to google /has/Member\n")
		directory := get_google_token()

		results, err := directory.Members.HasMember(group,user).Do()
		if err != nil {
          log.Printf("error asking google: %v\n", err)
	}
	log.Printf("CACHE - save response to cache - key: %s\n", key )
		c.Set(key,results.IsMember, cache.DefaultExpiration)
		return results.IsMember
	}

}
//##############################################################################
func check_access_by_member(user, authgroups_string string) (string, error) {
	// Checks whether the given user is a member of the group. Membership can be direct or nested.

	authgroups := strings.Split(authgroups_string, ";")
	//delete \n in last group
	authgroups[len(authgroups)-1] = strings.TrimSuffix(authgroups[len(authgroups)-1],"\n")

	// loop on authgroups
	for _, authgroup := range authgroups{
		if hasMember(user, authgroup){
			log.Printf("AUTH  -  %s isMember %s ? ...... return yes", user, authgroup)
			return "yes", nil
		}else{
			log.Printf("AUTH  - %s is Member %s ? ....... return no", user, authgroup)
		}
	}
	log.Printf("AUTH  - %s is not member of any groups return no", user)
	return "no", nil
}
//##############################################################################
func get_google_token() *admin.Service {
	jsonCredentials, err := ioutil.ReadFile(conf.ServiceAccountFile)
    if err != nil {
        log.Printf("error reading credentials from file: %v", err)
    }

    config, err := google.JWTConfigFromJSON(jsonCredentials, conf.GoogleScope)

    if err != nil {
            log.Printf("Unable to parse client secret file to config: %v", err)
    }

    config.Subject = conf.SubjectAccount
    ctx := context.Background()
    client := config.Client(ctx)
	srv, err := admin.New(client)

    if err != nil {
    	log.Printf("Unable to create directory service %v", err)
     }
	return srv


	}
//##############################################################################
func get_json(user string) (string, error)  {

	// TODO: ask cache
	log.Printf("CACHE - ask for JSON key: %s", user)
	val, found := c.Get(user)
	if found{
		log.Printf("CACHE - Found JSON key: %s in cache", user)
		//debug*** // fmt.Printf("z cache ------ %s\n",val.(string))
		return val.(string), nil
	}else {

		var wyniki []string

		// ask google
		log.Printf("CACHE - Do not found json for user %s \n", user)
		log.Printf("JSON  - connect to google \n")
		directory := get_google_token()

		results, err := directory.Groups.List().UserKey(strings.TrimSuffix(user, "\n")).Do()
		if err != nil {
			log.Printf("error asking google: %v\n", err)
			return "no", errors.New("Problem with asking google")

		}

		if len(results.Groups) == 0 {
			fmt.Print("No groups found.\n")
		} else {
			for _, u := range results.Groups {
				wyniki = append(wyniki, u.Email)
			}
		}
		jsonwynik, _ := json.Marshal(wyniki)
		log.Printf("CACHE - save JSON to cache - key: %s\n", user )
		c.Set(user,string(jsonwynik), cache.DefaultExpiration)
		return string(jsonwynik), nil
	}
}
//########################### GLOBAL ###########################################

var conf Configuration
var c *cache.Cache

//##############################################################################
func main() {
	//read config file---------------------------------------------------------------------
    config_file, _ := os.Open("config.json")
	defer config_file.Close()
	decoder := json.NewDecoder(config_file)
	err := decoder.Decode(&conf)
	if err != nil {
  	fmt.Println("error:", err)
	}
	//variables:
	//	conf.GoogleScope
	//  conf.ServiceAccountFile
	//	conf.SubjectAccount
	//	conf.LogFile
	//	conf.isBase64Encrypt

	//initialize cache ---------------------------------------------------------------------
	c = cache.New(5*time.Minute, 10*time.Minute)


	// open log file ---------------------------------------------------------------------
	f, err := os.OpenFile(conf.LogFile, os.O_RDWR | os.O_CREATE | os.O_APPEND, 0666)
	if err != nil {
    	log.Fatalf("error opening file: %v", err)
	}
	log.SetOutput(f)

	// request count---------------------------------------------------------------------
	counter := 0

	reader := bufio.NewReader(os.Stdin)

	for {
		counter += 1
		input, _ := reader.ReadString('\n')
		log.Println("############# request: ",counter, " ################")
		if strings.HasPrefix(input, "auth") {
			s := strings.Split(input, "#")
		 // s[0]="auth"; s[1]=user; s[2]=authgroups
			if len(s)==3 {
						log.Println("AUTH  - checking auth, user:(",s[1],") groups:",s[2])

	    			answer, err := check_access_by_member(s[1],s[2])
						if err != nil {
  						fmt.Println("error:", err)
						}
						log.Println("AUTH  - STDOUT: ", answer)
						fmt.Println(answer)
			}else{
				log.Println("AUTH  - Bad request, return NULL")
				fmt.Println("NULL")
			}
			continue
		}

		if strings.HasPrefix(input, "json") {
			s := strings.Split(input, "#")
			//s[0]="json"; s[1]=user;
			if len(s)==2 {
						log.Println("JSON  - fetch json, user:", s[1])

	    				answer, err := get_json(s[1])
						if err != nil {
  							log.Println("JSON  - error:", err)
  							fmt.Println("NULL")
  							continue
						}
						if conf.Base64Encrypt   {
							log.Println("JSON  - STDOUT: ", base64.StdEncoding.EncodeToString([]byte(answer)))
							fmt.Println(base64.StdEncoding.EncodeToString([]byte(answer)))
						}else {
							log.Println("JSON  - STDOUT: ", answer)
							fmt.Println(answer)
						}
			}else{
				log.Println("AUTH  - Bad request, return NULL")
				fmt.Println("NULL")
			}
		}else {
			log.Println("ERROR - bad request, return NULL")
			fmt.Println("NULL")
		}

	}
}

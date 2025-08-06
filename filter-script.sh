#!/bin/sh

if [ "$GIT_COMMITTER_NAME" = "ZANGARI-ADMINISTRADORA" ]
then
    export GIT_COMMITTER_NAME="ron"
    export GIT_COMMITTER_EMAIL="ronwsv@gmail.com"
fi
if [ "$GIT_AUTHOR_NAME" = "ZANGARI-ADMINISTRADORA" ]
then
    export GIT_AUTHOR_NAME="ron"
    export GIT_AUTHOR_EMAIL="ronwsv@gmail.com"
fi
